## MODIFIED Requirements

### Requirement: Persist successful Walk-forward runs and ordered windows
The system SHALL persist one `WalkForwardRun` parent row as a durable job before any Walk-forward window executes. The enqueue transaction SHALL validate and store the resolved configuration, base-strategy snapshot, provenance manifest, and checksums, and insert the parent with `status = "queued"`, a non-null `started_at`, null `finished_at`, placeholder `evidence_json`, and `window_count = 0`. A worker claim SHALL transition that same parent to `status = "running"` and record durable claim ownership. After every configured window and structured evidence calculation succeeds under that claim, the system SHALL update the same parent to `status = "success"`, set `finished_at`, `window_count`, and the final `evidence_json`, and persist one ordered child per selected OOS window with unique parent ordinal and unique `BacktestRun` ownership in the same publication transaction. If any execution, provenance, evidence, persistence, lost-claim, or retry-limit step fails, the system SHALL conditionally update the parent to `status = "failed"`, set `finished_at` and a bounded `error_message`, and persist no children from that failed attempt. Strategy and benchmark metrics remain owned by referenced OOS records. The HTTP service SHALL expose exactly one mutation route (`POST /api/walk-forwards/run`) that enqueues a new execution; it MUST NOT expose a client retry, edit, delete, claim, heartbeat, or status-mutation route.

#### Scenario: Queued parent exists before worker execution
- **WHEN** a valid Walk-forward execution is submitted
- **THEN** one parent row is committed with `status = "queued"`, non-null `started_at`, null `finished_at`, `window_count = 0`, and placeholder `evidence_json`
- **AND** that row has a positive id before any worker window backtest runs

#### Scenario: Complete run updates parent to success and creates ordered children
- **WHEN** a valid worker claim completes a Walk-forward execution successfully
- **THEN** the same parent row is updated to `status = "success"` with `finished_at`, final `window_count`, and final `evidence_json`
- **AND** one ordered child per selected OOS window is committed with unique parent ordinal and unique `BacktestRun` ownership

#### Scenario: Failed execution updates parent to failed without children
- **WHEN** a claimed Walk-forward execution fails before its final publication
- **THEN** the same parent row is updated to `status = "failed"` with `finished_at` and a bounded `error_message`
- **AND** no child rows from that failed attempt are persisted

#### Scenario: Complete run creates ordered children
- **WHEN** a Walk-forward execution completes successfully
- **THEN** one parent and one ordered child per selected OOS window are persisted

#### Scenario: Running parent row is persisted before windows execute
- **WHEN** a valid Walk-forward execution is enqueued
- **THEN** one parent row is persisted with `status = "queued"`, non-null `started_at`, null `finished_at`, `window_count = 0`, and placeholder `evidence_json`
- **AND** that row has a positive id before any worker window backtest runs

### Requirement: Query immutable Walk-forward history
Queries SHALL return current-strategy summaries with exact totals, bounded pagination, and chronological eager-loaded children. Queued and running records SHALL sort before terminal records by descending `started_at` then id; terminal records SHALL sort by descending `finished_at` then id. Every summary/detail SHALL expose status, attempt count, claimed timestamp, heartbeat timestamp, and lease expiry without exposing claim tokens or worker identities. Unknown or other-strategy ids return no result; legacy OOS runs do not fabricate history.

#### Scenario: Active job appears before terminal history
- **WHEN** a current-strategy queued or running record and completed history both exist
- **THEN** the active record is returned before terminal records
- **AND** it exposes its lifecycle timestamps and attempt count without a claim token or worker id

#### Scenario: Empty legacy history stays empty
- **WHEN** an upgraded database has OOS runs but no WF parent
- **THEN** history returns an empty collection and zero total

### Requirement: Failed Walk-forward executions leave a failed parent record
The parent and all source-side artifacts produced after a claim SHALL share the claimed worker's final publication transaction. Any execution, provenance, evidence, input-drift, or persistence failure that occurs after the queued parent was committed SHALL roll back all source-side OOS, signal, curve, and benchmark artifacts produced by that attempt, then conditionally update the matching parent claim to `status = "failed"` with `finished_at` and bounded `error_message`. A failed parent SHALL remain queryable; no children, OOS, signal, curve, or benchmark rows from the failed attempt SHALL remain. A failure before enqueue commits SHALL leave no persisted parent row.

#### Scenario: Late failure records failed parent and rolls back artifacts
- **WHEN** a later window or final persistence step fails under a valid claim
- **THEN** the parent row is conditionally updated to `status = "failed"` with `finished_at` and `error_message`
- **AND** no child, OOS, signal, curve, or benchmark row from that attempt is committed

#### Scenario: Preflight failure before queued row leaves no parent
- **WHEN** configuration or input preparation fails before the enqueue transaction commits
- **THEN** no `WalkForwardRun` parent row is persisted
- **AND** no source-side artifact is committed

#### Scenario: Preflight failure before running row leaves no parent
- **WHEN** configuration or input preparation fails before the `queued` parent row is committed
- **THEN** no `WalkForwardRun` parent row is persisted
- **AND** no source-side artifact is committed

### Requirement: Walk-forward run status is queryable and backfilled
`WalkForwardRun` SHALL expose a status constrained to `queued`, `running`, `success`, or `failed`; nullable `error_message`, `claimed_at`, `heartbeat_at`, `lease_expires_at`, `worker_id`, and `claim_token` columns; non-negative `attempt_count`; and nullable `finished_at`. The database SHALL enforce at most one `queued` or `running` parent per strategy and at most one `running` parent per SQLite database. The migration SHALL preserve existing successful and failed history, backfill legacy successful rows with terminal status and neutral lifecycle fields, and mark pre-migration `running` rows terminal failed with a bounded migration-interruption reason because they have no fencing token. It SHALL not alter existing child, OOS, signal, curve, or benchmark rows.

#### Scenario: Migration preserves historical terminal rows
- **WHEN** the durable-execution migration is upgraded against existing successful or failed Walk-forward history
- **THEN** every terminal row preserves its id, completion/evidence data, children, and terminal status
- **AND** its new claim lifecycle fields are null and attempt count is zero

#### Scenario: Migration closes unclaimed running rows
- **WHEN** the migration encounters a legacy `running` parent without a claim token
- **THEN** it changes that parent to `failed` with a bounded migration-interruption error and completion timestamp
- **AND** it does not automatically execute or duplicate that parent

#### Scenario: Migration backfills legacy success rows
- **WHEN** the Alembic revision is upgraded against a database with pre-Change `WalkForwardRun` rows
- **THEN** every existing row receives `status = "success"` and null `error_message`
- **AND** its existing `finished_at` value is preserved
- **AND** no child, OOS, signal, curve, or benchmark row is altered

#### Scenario: Downgrade drops status columns without losing legacy data
- **WHEN** the Alembic revision is downgraded
- **THEN** the `status`, `error_message`, and nullable-`finished_at` changes are reverted
- **AND** pre-existing parent and child rows remain otherwise unchanged

# walk-forward-evaluation-history Specification

## Purpose
Define the durable, immutable, provenance-bearing history of successful Walk-forward evaluations and their ordered OOS windows.
## Requirements
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

### Requirement: Configuration provenance uses an exact versioned identity
The parent SHALL persist the exact versioned configuration/provenance document and SHA-256 identity. New status-aware executions SHALL identify the resolved-session valuation/tradability policy version. Display paths MAY be retained but SHALL NOT affect identity; equal effective configuration and policy inputs produce equal checksums while repeated executions receive distinct run ids.

#### Scenario: Display path does not change identity
- **WHEN** equal effective configuration and policy input are loaded from different source paths
- **THEN** their effective configuration checksum is equal

#### Scenario: Resolution policy changes identity
- **WHEN** the status-aware valuation/tradability policy version differs
- **THEN** configuration/provenance identity differs even if YAML strategy values match

### Requirement: Input provenance is a compact bounded manifest
New executions SHALL persist `wf_provenance_v2`. Its manifest SHALL retain ordered ETF local ids and canonical identities, fund inception and listing dates, official sessions, following-session sentinel, raw and derived counts/bounds, supported status/source evidence summaries, resolution policy version, and checksum metadata without copying the complete raw price-value table. Query boundaries SHALL continue to accept valid `wf_provenance_v1` without fabricating v2 fields.

#### Scenario: Manifest excludes raw price table
- **WHEN** input provenance is persisted
- **THEN** it contains bounded manifest data and no full raw price-value array

#### Scenario: V2 manifest summarizes raw and derived sources
- **WHEN** status-aware input provenance is persisted
- **THEN** per-ETF and global raw/derived counts and bounds reconcile
- **AND** every derived record corresponds to one supported authoritative status

#### Scenario: Manifest excludes complete raw table
- **WHEN** v2 provenance is persisted
- **THEN** the bounded manifest contains no duplicate complete raw price array

#### Scenario: Legacy v1 remains readable
- **WHEN** history contains a valid `wf_provenance_v1` document
- **THEN** queries preserve its original semantics and do not add listing/status claims

### Requirement: Input checksum covers every effective database input
For `wf_provenance_v2`, the canonical input checksum SHALL cover policy version; ETF id/exchange/symbol, fund inception and listing dates; ordered official sessions and following-session sentinel; every effective raw `close_price`/`factor_hfq` row; and every effective status, reason, source, share ratio, resolution, and carried adjusted value. It SHALL exclude generated outputs, pre-listing rows, and future inputs. Valid legacy v1 checksums remain governed by their original contract.

#### Scenario: Effective input drift changes checksum
- **WHEN** an execution-sensitive input row changes
- **THEN** the input checksum changes

#### Scenario: Raw input drift changes checksum
- **WHEN** an effective raw price or factor changes
- **THEN** the v2 checksum changes

#### Scenario: Temporal evidence drift changes checksum
- **WHEN** listing date, status evidence, share ratio, resolution, or carried adjusted value changes
- **THEN** the v2 checksum changes

#### Scenario: Equal v2 inputs have stable checksum
- **WHEN** two executions have byte-equivalent canonical effective inputs under the same policy version
- **THEN** their input checksums are equal

#### Scenario: Invalid v2 reconciliation fails closed
- **WHEN** raw/derived ownership, ordering, date bounds, source-state exclusivity, carry ancestry, counts, or checksum do not reconcile
- **THEN** persistence and query validation reject the document

### Requirement: Versioned evidence round-trips without semantic loss
Persisted `wf_evidence_v1` SHALL validate at persistence, query and API boundaries and preserve all eight strategy summaries, rates, benchmark return/Tracking Error/Information Ratio groups, generalization gap and parameter stability. Unsupported versions or corrupt documents SHALL fail closed.

#### Scenario: Corrupt evidence fails closed
- **WHEN** a persisted evidence document has an unsupported version or invalid shape
- **THEN** typed reads raise a persisted-data contract error and return no partial evidence

### Requirement: Window selection evidence is bounded and reconciled
Each child SHALL persist boundaries, selected canonical parameters, candidate/eligible/skipped counts, fixed skip-reason counts, train Sharpe and OOS id. Counts and reasons SHALL reconcile; raw exception text, tracebacks, candidates and dynamic status strings MUST NOT be stored.

#### Scenario: Candidate counts reconcile
- **WHEN** candidates are skipped during selection
- **THEN** candidate count equals eligible plus skipped and reason counts equal skipped

### Requirement: Query immutable Walk-forward history
Queries SHALL return current-strategy summaries with exact totals, bounded pagination, and chronological eager-loaded children. Queued and running records SHALL sort before terminal records by descending `started_at` then id; terminal records SHALL sort by descending `finished_at` then id. Every summary/detail SHALL expose status, attempt count, claimed timestamp, heartbeat timestamp, and lease expiry without exposing claim tokens or worker identities. Unknown or other-strategy ids return no result; legacy OOS runs do not fabricate history.

#### Scenario: Active job appears before terminal history
- **WHEN** a current-strategy queued or running record and completed history both exist
- **THEN** the active record is returned before terminal records
- **AND** it exposes its lifecycle timestamps and attempt count without a claim token or worker id

#### Scenario: Empty legacy history stays empty
- **WHEN** an upgraded database has OOS runs but no WF parent
- **THEN** history returns an empty collection and zero total

### Requirement: Walk-forward history migration is non-destructive
The Alembic revision SHALL create only the WF parent/child tables, typed columns, checks, unique constraints, history index and foreign keys. It SHALL not backfill or alter existing backtest data; downgrade drops child before parent and preserves evidence owners.

#### Scenario: Migration preserves existing owners
- **WHEN** the WF revision is upgraded and downgraded around existing OOS data
- **THEN** pre-existing backtest, signal, curve and benchmark rows remain unchanged

### Requirement: Versioned history preserves benchmark-regime evidence
Newly persisted Walk-forward histories SHALL store `wf_evidence_v2`, containing all valid `wf_evidence_v1` content plus per-benchmark daily CAPM/monthly-capture aggregates and per-window daily-session or selected-month evidence counts defined by this Change. Persistence, query, and API boundaries SHALL validate `v2` strictly, continue to support legacy `v1`, and fail closed on unsupported versions, missing benchmark ownership, or corrupt metric/count relationships.

#### Scenario: New history round-trips v2 evidence
- **WHEN** a completed Walk-forward run with benchmark-regime metrics is persisted and queried in a fresh session
- **THEN** its `wf_evidence_v2` document round-trips every new aggregate, count, null, and evidence status
- **AND** referenced OOS benchmark rows retain the matching per-window source values

#### Scenario: Legacy v1 history remains readable
- **WHEN** a valid pre-change `wf_evidence_v1` history is queried
- **THEN** existing evidence remains readable
- **AND** no CAPM or capture value is fabricated

#### Scenario: Corrupt v2 history fails closed
- **WHEN** a `wf_evidence_v2` document has an unsupported benchmark key, invalid count, non-finite value, or source ownership mismatch
- **THEN** persistence or query rejects the complete history instead of returning partial evidence

### Requirement: Versioned history preserves tail-distribution evidence
After `add-benchmark-regime-performance-metrics`, newly persisted Walk-forward histories SHALL store `wf_evidence_v3`, containing all valid `wf_evidence_v2` content plus per-window and aggregate strategy/fixed-benchmark distribution metrics, counts, and evidence statuses. Persistence, query, and API SHALL validate v3 strictly, continue to support valid legacy v1/v2, and reject unsupported/corrupt documents without partial output.

#### Scenario: New v3 history round-trips source-owned evidence
- **WHEN** a completed Walk-forward run with distribution metrics is persisted and queried in a fresh session
- **THEN** every v3 value, null, count, status, benchmark key, and aggregate round-trips exactly
- **AND** referenced OOS records retain matching source fields

#### Scenario: Legacy v1 and v2 remain readable
- **WHEN** a valid earlier evidence document is queried
- **THEN** all evidence defined by that version remains readable
- **AND** no distribution metric or count is fabricated

#### Scenario: Corrupt v3 fails closed
- **WHEN** v3 contains an invalid version, owner, benchmark key, count relationship, non-finite value, loss invariant, or mismatch with referenced OOS fields
- **THEN** persistence or query rejects the complete history

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


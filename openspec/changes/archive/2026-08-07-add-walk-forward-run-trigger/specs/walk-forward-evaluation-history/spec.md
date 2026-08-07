## MODIFIED Requirements

### Requirement: Persist successful Walk-forward runs and ordered windows
The system SHALL persist one `WalkForwardRun` parent row at the start of every execution with `status = "running"`, a non-null `started_at`, a null `finished_at`, a placeholder `evidence_json`, `window_count = 0`, and the resolved configuration, base-strategy, provenance, manifest, and checksum fields. After every configured window and structured evidence calculation succeeds, the system SHALL update the same parent row to `status = "success"`, set `finished_at`, `window_count`, and the final `evidence_json`, and persist one ordered child per selected OOS window with unique parent ordinal and unique `BacktestRun` ownership. If any execution, provenance, evidence, or persistence step fails after the running row was committed, the system SHALL update the parent row to `status = "failed"`, set `finished_at` and `error_message`, and persist no children. Strategy and benchmark metrics remain owned by referenced OOS records. The HTTP service SHALL expose exactly one mutation route (`POST /api/walk-forwards/run`) that starts a new execution; the service MUST NOT expose any route that retries, edits, or deletes a `WalkForwardRun`, and the only update to a `WalkForwardRun` row permitted after the initial `running` insert is the runner-owned transition to `success` or `failed`.

#### Scenario: Running parent row is persisted before windows execute
- **WHEN** a Walk-forward execution is started
- **THEN** one parent row is persisted with `status = "running"`, non-null `started_at`, null `finished_at`, `window_count = 0`, and a placeholder `evidence_json`
- **AND** that row has a positive id before any window backtest runs

#### Scenario: Complete run updates parent to success and creates ordered children
- **WHEN** a Walk-forward execution completes successfully
- **THEN** the same parent row is updated to `status = "success"` with `finished_at`, final `window_count`, and final `evidence_json`
- **AND** one ordered child per selected OOS window is persisted with unique parent ordinal and unique `BacktestRun` ownership

#### Scenario: Failed execution updates parent to failed without children
- **WHEN** a Walk-forward execution fails after the running row was committed
- **THEN** the same parent row is updated to `status = "failed"` with `finished_at` and `error_message`
- **AND** no child rows are persisted for this run

#### Scenario: Complete run creates ordered children
- **WHEN** a Walk-forward execution completes successfully
- **THEN** one parent and one ordered child per selected OOS window are persisted

## REMOVED Requirements

### Requirement: Failed Walk-forward executions leave no history

## ADDED Requirements

### Requirement: Failed Walk-forward executions leave a failed parent record
Parent, children, selected OOS backtests and benchmarks SHALL share the caller-owned transaction for the source-side artifacts produced after the initial `running` row. Any execution, provenance, evidence, or persistence failure that occurs after the `running` parent row was committed SHALL update that parent row to `status = "failed"` with `finished_at` and `error_message`, commit that update, and roll back all source-side OOS, signal, curve, and benchmark artifacts produced by this command. The persisted `failed` parent row SHALL remain queryable so the API and CLI can report the failure; no children, OOS, signal, curve, or benchmark rows from the command SHALL remain. A failure that occurs before the `running` parent row is committed SHALL leave no persisted parent row.

#### Scenario: Late failure records failed parent and rolls back artifacts
- **WHEN** a later window or final persistence step fails after the `running` parent row was committed
- **THEN** the parent row is updated to `status = "failed"` with `finished_at` and `error_message` and committed
- **AND** no child, OOS, signal, curve, or benchmark row from the command is committed

#### Scenario: Preflight failure before running row leaves no parent
- **WHEN** configuration or input preparation fails before the `running` parent row is committed
- **THEN** no `WalkForwardRun` parent row is persisted
- **AND** no source-side artifact is committed

### Requirement: Walk-forward run status is queryable and backfilled
`WalkForwardRun` SHALL expose a `status` column constrained to `running`, `success`, or `failed`, a nullable `error_message` column, and a nullable `finished_at` column. The Alembic revision introducing these columns SHALL backfill every existing `WalkForwardRun` row (all of which were persisted only after successful completion before this Change) with `status = "success"` and null `error_message`, SHALL leave the existing non-null `finished_at` unchanged, SHALL NOT alter any existing child, OOS, signal, curve, or benchmark row, and SHALL support a downgrade that drops the new columns while preserving existing rows. Downgrade is permitted to lose the backfilled `status` information because pre-Change rows were unconditionally successful.

#### Scenario: Migration backfills legacy success rows
- **WHEN** the Alembic revision is upgraded against a database with pre-Change `WalkForwardRun` rows
- **THEN** every existing row receives `status = "success"` and null `error_message`
- **AND** its existing `finished_at` value is preserved
- **AND** no child, OOS, signal, curve, or benchmark row is altered

#### Scenario: Downgrade drops status columns without losing legacy data
- **WHEN** the Alembic revision is downgraded
- **THEN** the `status`, `error_message`, and nullable-`finished_at` changes are reverted
- **AND** pre-existing parent and child rows remain otherwise unchanged

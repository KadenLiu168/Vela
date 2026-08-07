## MODIFIED Requirements

### Requirement: Source writes use the caller transaction
The walk-forward runner SHALL persist a `WalkForwardRun` parent row with `status = "running"`, `started_at`, a placeholder `evidence_json`, `window_count = 0`, and the resolved configuration/provenance/manifest/checksum fields at the start of execution, and SHALL commit that row through the caller-provided source session to obtain a positive `walk_forward_run_id` before executing any window. After every window, OOS evaluation, benchmark evaluation, provenance/evidence validation, and child persistence step succeeds, the runner SHALL update the same parent row to `status = "success"`, set `finished_at`, `window_count`, and the final `evidence_json`, and persist one ordered child per selected OOS window, then commit through the caller-provided source session. If any window, OOS evaluation, fixed benchmark evaluation, provenance/evidence, or persistence step fails after the running row was committed, the runner SHALL update the parent row to `status = "failed"`, set `finished_at` and `error_message`, commit that update through the caller-provided source session, and re-raise so the caller can map the error. The runner SHALL NOT roll back the running or failed parent row; OOS backtest rows, signal rows, curve rows, and benchmark rows added to the source session before the failure SHALL be rolled back by the caller-managed transaction boundary so only the parent `WalkForwardRun` row (in `running` or `failed` state) remains. The CLI SHALL continue to execute the complete run inside the repository's managed-session boundary and SHALL print the `walk_forward_run_id` and report on success; on failure the CLI SHALL exit non-zero and the parent row SHALL remain persisted in `failed` state.

#### Scenario: Complete run commits source outputs
- **WHEN** all windows, OOS evaluations, and fixed benchmark evaluations succeed through the CLI or API
- **THEN** the runner commits the initial `running` parent row, then the final `success` parent update with children, in the managed caller transaction

#### Scenario: Later window failure rolls back source outputs
- **WHEN** a later OOS or fixed benchmark evaluation fails after an earlier window added source-side rows
- **THEN** the runner updates the parent row to `status = "failed"` with `finished_at` and `error_message` and commits that update
- **AND** the caller-managed transaction rolls back the source-side OOS, signal, curve, and benchmark rows from this command
- **AND** the parent `WalkForwardRun` row remains persisted in `failed` state with no children

#### Scenario: Final WF persistence failure rolls back OOS outputs
- **WHEN** every OOS window succeeds but the final parent or child validation/flush fails after the running row was committed
- **THEN** the runner updates the parent row to `status = "failed"` and rolls back all WF history and selected OOS artifacts from the command

#### Scenario: Preflight failure records failed state without running windows
- **WHEN** configuration, provenance, or input preparation fails before any window executes
- **THEN** the runner records `status = "failed"` with `error_message` on the parent row (or no parent row is persisted if the failure precedes the running-row insert)
- **AND** no OOS backtest, signal, curve, or benchmark row is added

### Requirement: Successful runner execution returns flushed evaluation identity
The runner SHALL commit the initial `WalkForwardRun` parent row with `status = "running"` through the caller-provided source session, flush it to obtain a positive parent id, and return that id with the report/result after the final `status = "success"` update is committed. A `running` id MAY be returned to the caller (for example the API run-trigger endpoint) before the run completes so the caller can poll the detail endpoint; the CLI SHALL wait for completion and return the final id only. No id SHALL be returned for a failure that prevents the initial running row from being persisted.

#### Scenario: Runner returns parent id before caller commit
- **WHEN** the API run-trigger endpoint starts a walk-forward execution and the initial running row is committed and flushed
- **THEN** the runner makes the positive parent id available to the endpoint before completion
- **AND** the CLI, on success, returns the final parent id after the `status = "success"` commit

#### Scenario: CLI returns final id after success
- **WHEN** the CLI executes a walk-forward run and every window and evidence calculation succeeds
- **THEN** the runner returns the positive Walk-forward parent id after the final `status = "success"` commit
- **AND** the CLI prints that id and the report

## MODIFIED Requirements

### Requirement: Source writes use the caller transaction
The walk-forward runner SHALL execute only for a persisted `WalkForwardRun` that a worker or synchronous CLI has claimed with a current opaque claim token. It SHALL use the queued resolved configuration, base-strategy snapshot, provenance manifest, and checksums, and SHALL reject a preflight manifest/checksum mismatch before any source-side OOS output. After every window, OOS evaluation, benchmark evaluation, provenance/evidence validation, and child persistence step succeeds, the runner SHALL persist one ordered child per selected OOS window and conditionally update the same parent from `running` to `success`, setting `finished_at`, `window_count`, and final `evidence_json`, in one caller-managed source transaction. If a window, OOS evaluation, fixed benchmark evaluation, provenance/evidence, persistence, or ownership step fails, the runner SHALL roll back OOS backtest rows, signal rows, curve rows, and benchmark rows added by that attempt, then conditionally update the matching claimed parent to `failed`, set `finished_at` and bounded `error_message`, and re-raise. A runner that no longer owns the claim SHALL roll back and raise a lost-claim error; it SHALL not change parent status. The CLI SHALL execute the complete claimed run through the repository's managed-session boundary and print the run id and report only on success.

#### Scenario: Complete run commits source outputs
- **WHEN** all windows, OOS evaluations, and fixed benchmark evaluations succeed under a valid claim
- **THEN** the runner commits the final `success` parent update with children in the same transaction as all selected source outputs

#### Scenario: Later window failure rolls back source outputs
- **WHEN** a later OOS or fixed benchmark evaluation fails after an earlier window added source-side rows
- **THEN** the runner records `status = "failed"` only if it still owns the matching claim
- **AND** the caller-managed transaction rolls back source-side OOS, signal, curve, and benchmark rows from that attempt
- **AND** the parent `WalkForwardRun` remains persisted in failed state with no children from that attempt

#### Scenario: Final WF persistence failure rolls back OOS outputs
- **WHEN** every OOS window succeeds but the final parent or child validation/flush fails
- **THEN** the runner records `status = "failed"` only if it still owns the claim
- **AND** rolls back all selected OOS artifacts from the attempt

#### Scenario: Preflight failure records failed state without running windows
- **WHEN** queued-input revalidation fails before any window executes
- **THEN** the runner records `status = "failed"` only if it owns the matching claim
- **AND** no OOS backtest, signal, curve, or benchmark row is added

### Requirement: Successful runner execution returns flushed evaluation identity
The enqueue service SHALL return a positive `WalkForwardRun` id only after the queued parent has committed. `WalkForwardRunner` SHALL accept that existing claimed id and return it with the report only after its conditional `status = "success"` update has committed. It SHALL not create a second parent, return an id for an uncommitted enqueue, or publish a result after it loses its claim. The API returns the queued id before completion; the synchronous CLI waits for a terminal result.

#### Scenario: API returns queued parent identity before execution
- **WHEN** a valid API submission commits a queued parent
- **THEN** the enqueue service makes that positive parent id available before worker completion
- **AND** no Walk-forward window has executed in the API process

#### Scenario: CLI returns final id after success
- **WHEN** the CLI executes a claimed Walk-forward run and every window and evidence calculation succeeds
- **THEN** the runner returns the same positive queued parent id after the final `status = "success"` commit
- **AND** the CLI prints that id and the report

#### Scenario: Runner returns parent id before caller commit
- **WHEN** the API enqueue endpoint commits a queued Walk-forward parent and a worker claims it
- **THEN** the enqueue service makes the positive parent id available to the endpoint before worker completion
- **AND** the CLI, on success, returns the final parent id after the `status = "success"` commit

### Requirement: CLI command
The system SHALL provide a `vela walk-forward` CLI command that accepts a walk-forward YAML configuration path, an optional database URL using the same default as other database commands, and an optional report output path. Relative base-strategy paths in the walk-forward YAML SHALL resolve relative to that YAML file. The command SHALL enqueue a durable execution and claim/run that exact record synchronously against SQLite only; it SHALL not bypass the durable claim protocol.

#### Scenario: CLI invocation
- **WHEN** the user runs `vela walk-forward --config config/walk_forward_v1.yaml`
- **THEN** the system enqueues and claims one Walk-forward record, executes it, prints the report to stdout, and exits with code 0 on success

#### Scenario: CLI with invalid config
- **WHEN** the user runs `vela walk-forward --config nonexistent.yaml`
- **THEN** the system exits with a non-zero code and prints an error message indicating the config file could not be found

#### Scenario: Report output file
- **WHEN** the user supplies `--output /tmp/walk-forward-report.txt`
- **THEN** the command writes the same complete report to that path and prints a confirmation

#### Scenario: Non-SQLite database rejected
- **WHEN** the user supplies a non-SQLite database URL
- **THEN** the command fails before any backtest with a clear SQLite-only message

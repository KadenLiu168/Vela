## ADDED Requirements

### Requirement: Runner prepares provenance before source output
Before starting any source-side OOS backtest, `WalkForwardRunner` SHALL validate every generated candidate, resolve each valid strategy's non-negative lookback, load `TradingCalendar` as the sole window/session axis, generate the final windows and build the complete `wf_provenance_v1` configuration/input manifest and checksums. It MUST NOT derive windows from `MarketPrice.trade_date` or fall back between calendar and price sources. No valid candidate, invalid lookback, incomplete official-session envelope or missing required price SHALL fail before source output is added.

#### Scenario: Maximum valid-candidate lookback bounds provenance
- **WHEN** valid candidates declare different strategy lookbacks
- **THEN** provenance begins at the exact official session required by the maximum lookback
- **AND** covers every input reachable by any candidate through the configured end

#### Scenario: Preflight failure precedes OOS persistence
- **WHEN** configuration or input provenance cannot be completed
- **THEN** the runner raises before invoking a source-side OOS backtest
- **AND** no source signal, run, curve or benchmark is added

#### Scenario: Missing price dates cannot redefine windows
- **WHEN** `MarketPrice` dates are incomplete or include a non-official date while `TradingCalendar` supplies the configured official sequence
- **THEN** window boundaries are derived only from `TradingCalendar`
- **AND** normal backtest completeness validation fails any required official price gap

### Requirement: Successful runner execution returns flushed evaluation identity
After producing valid `wf_evidence_v1`, `WalkForwardRunner` SHALL persist the parent and ordered window records through the caller-provided session, flush them without committing or rolling back that session, and return the positive Walk-forward parent id with the report/result. No id SHALL be returned for a failed execution; a flushed id is not durable until the caller commits.

#### Scenario: Runner returns parent id before caller commit
- **WHEN** every window and evidence calculation succeeds and parent/children flush
- **THEN** the runner returns a positive Walk-forward evaluation id
- **AND** leaves final commit ownership to the caller

#### Scenario: Runner failure has no returned evaluation id
- **WHEN** any window, fixed benchmark, provenance, evidence validation or persistence step fails
- **THEN** the runner raises the failure
- **AND** does not return a Walk-forward evaluation id

### Requirement: Runner records bounded candidate selection evidence
For each window the runner SHALL persist generated candidate count, eligible successful non-null-Sharpe count, skipped count and a fixed-category reason map. Candidate count SHALL equal eligible plus skipped count; reason counts SHALL sum to skipped count. The only persisted reason keys SHALL be `invalid_config`, `training_error`, `training_non_success` and `missing_train_sharpe`. It MUST NOT persist raw exception text, tracebacks, dynamic statuses, candidate payloads or every training backtest.

#### Scenario: Candidate counts reconcile
- **WHEN** a window generates ten candidates and three become eligible scored results
- **THEN** candidate count is ten, eligible count is three and skipped count is seven
- **AND** the fixed reason counts sum to seven
- **AND** the selected candidate remains identifiable by canonical parameters

#### Scenario: Failure detail remains bounded
- **WHEN** one candidate raises an exception with multiline dynamic text
- **THEN** that candidate increments only `training_error`
- **AND** no raw exception content is persisted

## MODIFIED Requirements

### Requirement: Source writes use the caller transaction
The walk-forward runner SHALL neither commit nor roll back the caller-provided source session. The CLI SHALL execute the complete run inside the repository's managed-session boundary so all selected OOS runs, fixed benchmark results and the final Walk-forward parent/children commit only after every window, provenance/evidence validation and persistence step succeeds. Any later OOS, fixed benchmark, provenance, evidence or WF persistence failure SHALL roll back all writes from the command.

#### Scenario: Complete run commits source outputs and history
- **WHEN** all windows, OOS evaluations, fixed benchmark evaluations, evidence validation and WF persistence succeed through the CLI
- **THEN** the managed caller transaction commits all source-side outputs and one complete WF history once

#### Scenario: Later window failure rolls back source outputs
- **WHEN** a later OOS or fixed benchmark evaluation fails after an earlier window added source-side rows
- **THEN** the CLI exits non-zero and the managed caller transaction persists none of this command's source-side rows or WF history

#### Scenario: Final WF persistence failure rolls back OOS outputs
- **WHEN** every OOS window succeeds but final parent/child validation or flush fails
- **THEN** the managed caller transaction persists neither WF history nor any selected OOS artifact from the command

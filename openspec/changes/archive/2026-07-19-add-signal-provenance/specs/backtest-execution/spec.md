## ADDED Requirements

### Requirement: Backtest provenance linkage is complete and atomic

`run_backtest` SHALL persist every generated historical signal with `source="backtest"`, capture every returned persisted signal id, and link exactly those signals to the newly created `backtest_run` before the caller-managed transaction commits.

#### Scenario: Completed run links every produced signal
- **WHEN** a backtest completes signal generation and result persistence
- **THEN** every persisted signal produced by that execution has `source="backtest"`
- **AND** every such signal has `backtest_run_id` equal to the new run id
- **AND** no signal outside that execution receives the new run id

#### Scenario: Missing persisted signal id aborts the run
- **WHEN** historical generation returns any result without a persisted `strategy_signal_id`
- **THEN** `run_backtest` raises before the transaction commits
- **AND** callers using the project's managed session boundary commit neither the new run nor any signals from that failed execution

#### Scenario: Link mismatch aborts the run
- **WHEN** the linkage update cannot match every distinct captured signal id as an unlinked backtest signal
- **THEN** the linkage helper raises instead of silently accepting a partial update
- **AND** callers using the project's managed session boundary roll back the signals, run, curve rows, and linkage together

#### Scenario: Concurrent or repeated runs do not cross-link signals
- **WHEN** two backtests execute for the same strategy, config version, and date range
- **THEN** each run links only the primary-key ids captured by that execution
- **AND** neither run rewrites signals already linked to another run

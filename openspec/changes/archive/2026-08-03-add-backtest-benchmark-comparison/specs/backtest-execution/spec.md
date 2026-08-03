## ADDED Requirements

### Requirement: Benchmark-enabled backtest orchestration
Normal `run_backtest` execution SHALL calculate the two fixed benchmarks from validated local inputs before persisting the completed run. Internal training calls used by Walk-forward parameter selection SHALL be able to skip benchmark calculation; selected OOS and normal runs SHALL not skip it.

#### Scenario: Normal run persists strategy and benchmarks together
- **WHEN** a normal backtest completes with complete local data
- **THEN** it calculates the strategy curve and both benchmark curves
- **AND** it persists their results within the caller-managed transaction

#### Scenario: Training run skips benchmark work
- **WHEN** Walk-forward evaluates a parameter combination on an IS training window
- **THEN** it evaluates the strategy Sharpe without calculating or persisting benchmark results

#### Scenario: OOS run includes benchmarks
- **WHEN** Walk-forward evaluates the selected parameter combination on an OOS window
- **THEN** it calculates and persists both fixed benchmark results for that window

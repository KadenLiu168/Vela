## ADDED Requirements

### Requirement: Expanded performance metrics are calculated and persisted atomically
Benchmark-enabled execution SHALL validate benchmark identity and official-session price completeness and construct benchmark curves before strategy signal generation. After the strategy curve exists, normal success/partial and selected Walk-forward OOS backtests SHALL calculate expanded strategy metrics, benchmark metrics and aligned TE/IR before result persistence. Internal Walk-forward training trials that skip benchmarks SHALL calculate strategy-only expanded metrics inside their isolated training snapshot. `run_backtest` MUST NOT commit or roll back the caller's transaction; the caller-managed boundary SHALL commit or roll back signals, runs, curves, existing metrics, expanded metrics and metric-version snapshots together.

#### Scenario: Successful run persists one metric version
- **WHEN** a normal backtest completes successfully
- **THEN** its strategy and both benchmark records persist every calculable expanded metric atomically
- **AND** its parameter snapshot records `performance_metrics_v1`

#### Scenario: Partial run persists the calculated strategy and benchmark set
- **WHEN** a normal benchmark-enabled backtest reaches metric calculation and completes with `partial` status
- **THEN** its calculable strategy and benchmark expanded metrics persist atomically
- **AND** its parameter snapshot records `performance_metrics_v1`

#### Scenario: Training run calculates only isolated strategy metrics
- **WHEN** Walk-forward evaluates a parameter combination with benchmark calculation disabled
- **THEN** it calculates strategy Sortino, Calmar and duration and records `performance_metrics_v1` in the training snapshot
- **AND** no training run, benchmark or expanded metric is persisted to the source database

#### Scenario: Missing benchmark input still fails before signals
- **WHEN** a benchmark-enabled run lacks required benchmark identity or an official-session price
- **THEN** it fails before strategy signal generation and before any result artifact is flushed

#### Scenario: Late active-metric failure rolls back the caller transaction
- **WHEN** aligned active-risk calculation fails after strategy signals have been flushed but before result persistence
- **THEN** `run_backtest` propagates the failure without committing or rolling back independently
- **AND** the caller-managed transaction rolls back every signal, run, strategy curve, benchmark and benchmark curve from that attempt

#### Scenario: Existing metric values are preserved
- **WHEN** the runner adds the expanded calculations
- **THEN** existing total return, CAGR, maximum drawdown, volatility and Sharpe values remain unchanged

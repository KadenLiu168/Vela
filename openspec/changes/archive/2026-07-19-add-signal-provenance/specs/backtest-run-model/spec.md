## ADDED Requirements

### Requirement: Backtest run exposes its strategy signals

The ORM SHALL expose a bidirectional relationship between `BacktestRun` and `StrategySignal` through `StrategySignal.backtest_run_id`.

#### Scenario: Run exposes ordered signals
- **WHEN** backend code loads a backtest run with linked strategy signals
- **THEN** `BacktestRun.signals` contains only signals whose `backtest_run_id` equals that run id
- **AND** the signals are ordered by `signal_date` ascending then `id` ascending

#### Scenario: Signal exposes its run
- **WHEN** backend code loads a strategy signal with a non-null `backtest_run_id`
- **THEN** `StrategySignal.backtest_run` resolves to that run

#### Scenario: Persisted backtest query loads signals
- **WHEN** backend code calls `get_backtest_result` for an existing run
- **THEN** the returned run has both its ordered `equity_curve` and ordered `signals` collections available

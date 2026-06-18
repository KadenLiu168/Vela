## Why

Vela needs durable backtest run storage before historical backtesting can preserve comparable results across strategy versions, parameter sets, and date ranges. The first persistence contract should record enough run metadata, metrics, and equity curve data for later analysis without implementing the backtest engine yet.

## What Changes

- Add a SQLAlchemy `BacktestRun` ORM model for one historical backtest execution.
- Record strategy name, configuration version, requested backtest date range, serialized parameter snapshot, lifecycle status, optional error message, and audit timestamps.
- Store core performance metrics on the run: total return, annualized return, maximum drawdown, Sharpe ratio, and volatility.
- Allow multiple runs for the same strategy, configuration version, and date range so retries and parameter experiments are preserved.
- Add a SQLAlchemy `BacktestEquityPoint` ORM model for daily net value points associated with a backtest run.
- Prevent duplicate equity curve points for the same run and trading date.

## Capabilities

### New Capabilities

- `backtest-run-model`: SQLAlchemy ORM models and persistence contract for backtest runs and their equity curve data.

### Modified Capabilities

None.

## Impact

- Core models: adds `BacktestRun` and `BacktestEquityPoint` under `packages/core/src/vela_core/models`.
- Alembic: adds a migration for the new backtest tables, constraints, and indexes.
- Tests: adds focused model and migration-adjacent schema coverage under `packages/core/tests`.
- APIs: no repository layer, service layer, CLI, or backtest calculation API changes in this proposal.
- Dependencies: no new runtime dependencies.

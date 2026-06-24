## Why

COP-65 needs a user-facing `run-backtest` command that turns the existing signal generation, equity curve, metrics, and persistence helpers into one runnable workflow. Without this command, contributors can build individual pieces but cannot run and store a backtest from the CLI.

## What Changes

- Add a core backtest runner that loads local trading dates for a requested date range.
- Generate historical strategy signals as part of the backtest workflow.
- Calculate equity curve, annualized return, maximum drawdown, volatility, and Sharpe ratio.
- Persist the backtest run and normalized equity curve rows.
- Add a `run-backtest` CLI command that accepts database URL, strategy config path, start date, and end date.
- Print a concise core metric summary including persisted run id.

## Capabilities

### New Capabilities

- `backtest-execution`: End-to-end backtest orchestration using local market data, strategy configuration, generated historical signals, metric calculation, and result persistence.

### Modified Capabilities

- `cli-database-initialization`: Expose `run-backtest` through the project CLI.

## Impact

- Code: add a core backtest runner and extend the CLI entrypoint.
- Tests: add core runner tests and CLI command tests.
- OpenSpec: add `backtest-execution` spec and update CLI spec.
- No database migration is needed.

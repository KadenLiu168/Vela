## Why

COP-64 needs a focused way to persist completed backtest results after existing calculation helpers produce metrics and curve data. The ORM tables already exist, but callers currently have to hand-wire `BacktestRun` and `BacktestEquityCurve` rows.

## What Changes

- Add a core backtest result persistence helper that creates a new `BacktestRun` for each call.
- Persist associated `BacktestEquityCurve` rows for the newly created run.
- Add a query helper that loads a backtest run with its equity curve for later analysis.
- Keep the scope limited to persistence of already-computed results; do not implement a backtest runner or update existing runs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `backtest-run-model`: Add service-level persistence and query behavior for backtest result rows.

## Impact

- Code: add a core persistence module and export it from `vela_core`.
- Tests: add focused persistence tests using the existing in-memory SQLite pattern.
- OpenSpec: extend `backtest-run-model` with result persistence and query requirements.
- No database migration is needed because `BacktestRun` and `BacktestEquityCurve` already exist.

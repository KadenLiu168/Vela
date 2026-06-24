## 1. Persistence API

- [x] 1.1 Add typed dataclass inputs for backtest run data and equity curve row data.
- [x] 1.2 Implement `persist_backtest_result` to create a new `BacktestRun` and related `BacktestEquityCurve` rows.
- [x] 1.3 Implement `get_backtest_result` to load one run by id with ordered equity curve rows.
- [x] 1.4 Export the persistence input/result types and helper functions from `vela_core`.

## 2. Tests

- [x] 2.1 Add tests proving run metadata, parameters, metrics, and curve rows are persisted.
- [x] 2.2 Add a test proving repeated persistence creates separate runs for the same strategy/config/date range.
- [x] 2.3 Add tests proving persisted results can be queried with ordered curve rows and missing ids return no result.

## 3. Verification

- [x] 3.1 Run targeted tests for backtest result persistence.
- [x] 3.2 Run full tests, lint, type check, and OpenSpec validation.

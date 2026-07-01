## 1. API Contract Tests

- [x] 1.1 Add an API integration test that runs a backtest through `POST /api/backtests/run` using temporary SQLite data and verifies persisted `BacktestRun` and `BacktestEquityCurve` rows.
- [x] 1.2 Add request validation tests for invalid or missing run backtest date inputs.

## 2. API Implementation

- [x] 2.1 Add the run backtest endpoint to `apps/api/src/vela_api/main.py`.
- [x] 2.2 Serialize `BacktestRunResult` fields consistently with existing API decimal/date responses.

## 3. Validation

- [x] 3.1 Run focused API tests and relevant backtest tests.
- [x] 3.2 Run ruff checks, feasible full tests, and OpenSpec validation.

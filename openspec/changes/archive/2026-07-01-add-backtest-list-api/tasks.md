## 1. API Coverage

- [x] 1.1 Add API integration tests for `GET /api/backtests` with multiple persisted `BacktestRun` rows, expected recency ordering, response fields, and decimal/timestamp formatting.
- [x] 1.2 Add API integration tests for `limit` and empty-list behavior.

## 2. API Implementation

- [x] 2.1 Implement `GET /api/backtests` using the request-scoped database session and a real `BacktestRun` query ordered by `started_at` and `id`.
- [x] 2.2 Format list items with run id, date range, status, start/end timestamps, and core metric fields without returning equity curve data.

## 3. Validation

- [x] 3.1 Run targeted API tests for the backtest endpoints.
- [x] 3.2 Run repository validation commands, including relevant/all tests, ruff check, ruff format check, and OpenSpec validation.

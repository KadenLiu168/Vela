## ADDED Requirements

### Requirement: API run backtest endpoint
The API service SHALL expose a run backtest command endpoint at `POST /api/backtests/run`.

#### Scenario: Run backtest for explicit date range
- **WHEN** a client sends `POST /api/backtests/run?startDate=2026-01-01&endDate=2026-01-31`
- **THEN** the API calls the existing core `run_backtest` capability for that date range
- **AND** the response status is 200
- **AND** the response includes run id, status, start date, end date, trading day count, signal count, total return, annualized return, max drawdown, volatility, and Sharpe ratio

#### Scenario: Reject invalid backtest date range
- **WHEN** a client sends `POST /api/backtests/run` with `startDate` after `endDate`
- **THEN** the API rejects the request without persisting a backtest run

#### Scenario: No JSON body schema
- **WHEN** a client calls the run backtest endpoint
- **THEN** the endpoint accepts `startDate` and `endDate` only as required query parameters

### Requirement: API run backtest integration validation
The API run backtest endpoint SHALL be validated with the local API app, a temporary SQLite database, and the existing backend backtest workflow.

#### Scenario: Run backtest endpoint persists SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/backtests/run` with a valid date range
- **THEN** the response contains values produced by the existing core backtest workflow
- **AND** the generated `BacktestRun` and `BacktestEquityCurve` rows are persisted in SQLite
- **AND** the validation does not rely only on mocked backtest results

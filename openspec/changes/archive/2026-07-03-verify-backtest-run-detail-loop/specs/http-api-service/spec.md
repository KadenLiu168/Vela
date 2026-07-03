## ADDED Requirements

### Requirement: API backtest run to detail closed-loop validation
The API service SHALL validate that a successful run-backtest request persists a backtest result that is visible through the backtest detail API from the same local SQLite database.

#### Scenario: Run endpoint updates backtest detail read state
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/backtests/run` with a valid date range
- **AND** the client then sends `GET /api/backtests/{run_id}` for the returned run id against the same API app and database
- **THEN** the run response reports values produced by the existing backtest workflow
- **AND** the generated `BacktestRun` and ordered `BacktestEquityCurve` rows are persisted in SQLite
- **AND** the detail response identifies the same run id
- **AND** the detail response includes metric cards source data and equity curve rows for the generated run

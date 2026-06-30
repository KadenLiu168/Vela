## ADDED Requirements

### Requirement: API dashboard empty workflow validation
The API service SHALL validate that `GET /api/dashboard` returns empty workflow values from a real empty local SQLite database.

#### Scenario: Dashboard endpoint returns empty workflow data
- **WHEN** an API integration test configures the app with a temporary SQLite database containing no market prices, successful signals, or backtests
- **THEN** `GET /api/dashboard` returns zero market price rows
- **AND** it returns zero covered ETFs
- **AND** it returns null latest signal data
- **AND** it returns null recent backtest data
- **AND** the validation does not rely on mocked dashboard data

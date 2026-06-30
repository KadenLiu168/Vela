## MODIFIED Requirements

### Requirement: API dashboard aggregate endpoint
The API service SHALL expose `GET /api/dashboard` as a read-only endpoint that returns the local Dashboard aggregate state.

#### Scenario: Dashboard endpoint returns aggregate state
- **WHEN** a client sends `GET /api/dashboard`
- **THEN** the response status is 200
- **AND** the response includes strategy summary, market data status, latest successful signal summary, and recent backtest summary fields

#### Scenario: Dashboard endpoint uses request database session
- **WHEN** the dashboard endpoint builds market, signal, and backtest summary data
- **THEN** it uses the API request-scoped database session dependency
- **AND** it delegates aggregation behavior to the core dashboard aggregation service

### Requirement: API dashboard integration validation
The dashboard endpoint SHALL be validated against a real local SQLite database and existing ORM models.

#### Scenario: Dashboard endpoint reads persisted SQLite rows
- **WHEN** a test API app is configured with a temporary SQLite database containing `MarketPrice`, `StrategySignal`, and `BacktestRun` rows
- **THEN** `GET /api/dashboard` returns aggregate values derived from those persisted rows
- **AND** the latest signal summary uses the latest successful persisted signal
- **AND** the latest signal summary includes fallback status derived from persisted `StrategySignalPosition` rows
- **AND** the validation does not rely only on mocked dashboard data

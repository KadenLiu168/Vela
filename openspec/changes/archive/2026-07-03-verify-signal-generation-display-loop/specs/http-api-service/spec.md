## ADDED Requirements

### Requirement: API signal generation to display data-source closed-loop validation
The API service SHALL validate that a successful signal generation request persists a strategy signal that is visible through both latest signal and Dashboard aggregate reads from the same local SQLite database.

#### Scenario: Generate endpoint updates latest signal and dashboard aggregate state
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/strategy-signals/generate`
- **AND** the client then sends `GET /api/strategy-signals/latest` and `GET /api/dashboard` against the same API app and database
- **THEN** the generate response reports values produced by the existing strategy signal generation workflow
- **AND** the generated `StrategySignal` and `StrategySignalPosition` rows are persisted in SQLite
- **AND** the latest signal response identifies the generated signal and target positions
- **AND** the Dashboard latest signal summary identifies the same generated signal and target holding count

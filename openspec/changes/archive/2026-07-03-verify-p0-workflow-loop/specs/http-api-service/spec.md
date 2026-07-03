## ADDED Requirements

### Requirement: API full P0 workflow closed-loop validation
The API service SHALL validate the full P0 workflow through real API endpoints and a shared local SQLite database.

#### Scenario: P0 workflow persists and restores backend state
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client reads `GET /api/dashboard`
- **AND** the client sends `POST /api/market-data/fetch`, `POST /api/strategy-signals/generate`, and `POST /api/backtests/run` in sequence
- **AND** the client then reads `GET /api/dashboard`, `GET /api/strategy-signals/latest`, and `GET /api/backtests/{run_id}` against the same API app and database
- **THEN** each operation response reports values produced by the existing backend workflows
- **AND** the refreshed Dashboard response includes persisted market data, latest signal, recent backtest, and fetch log state
- **AND** the latest signal response identifies the generated signal
- **AND** the backtest detail response identifies the generated backtest run and includes equity curve rows
- **AND** the validation records any backend capability gap or API field mismatch found during the workflow

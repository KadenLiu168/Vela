## ADDED Requirements

### Requirement: API market data fetch to dashboard closed-loop validation
The API service SHALL validate that a successful market data fetch is visible through the Dashboard aggregate when both requests use the same local SQLite database.

#### Scenario: Fetch endpoint updates dashboard aggregate state
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and a local market price baseline
- **AND** the test provider returns deterministic daily prices for the requested ETF
- **AND** the client sends `POST /api/market-data/fetch?mode=incremental`
- **AND** the client then sends `GET /api/dashboard` against the same API app and database
- **THEN** the fetch response reports counts produced by the existing market data fetch workflow
- **AND** the fetched market prices and fetch log are persisted in SQLite
- **AND** the Dashboard response reports market data status from the newly persisted market prices
- **AND** the Dashboard response includes the latest fetch log summary for the fetch operation

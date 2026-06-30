## ADDED Requirements

### Requirement: API market data fetch endpoint
The API service SHALL expose a market data fetch command endpoint that frontend clients can call with `mode=incremental` or `mode=full`.

#### Scenario: Fetch incremental market data
- **WHEN** a client sends `POST /api/market-data/fetch?mode=incremental`
- **THEN** the API calls the existing incremental market price fetch workflow
- **AND** the response status is 200
- **AND** the response includes fetch status, requested ETF count, fetched row count, inserted row count, updated row count, failed symbols, and error message

#### Scenario: Fetch full market data
- **WHEN** a client sends `POST /api/market-data/fetch?mode=full`
- **THEN** the API calls the existing full market price fetch workflow
- **AND** the response status is 200
- **AND** the response includes fetch status, requested ETF count, fetched row count, inserted row count, updated row count, failed symbols, and error message

#### Scenario: Reject invalid fetch mode
- **WHEN** a client sends `POST /api/market-data/fetch` with a `mode` other than `incremental` or `full`
- **THEN** the API rejects the request before running a market data fetch workflow

### Requirement: API market data fetch integration validation
The API market data fetch endpoint SHALL be validated with a real request-scoped database session, a temporary SQLite database, and a controlled market data provider.

#### Scenario: Fetch endpoint persists provider rows to SQLite
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and a local market price baseline
- **AND** the test provider returns deterministic daily prices for the requested ETF
- **THEN** `POST /api/market-data/fetch?mode=incremental` returns counts derived from the existing fetch workflow
- **AND** the fetched market prices and fetch log are persisted in SQLite
- **AND** the validation does not rely only on mocked workflow results

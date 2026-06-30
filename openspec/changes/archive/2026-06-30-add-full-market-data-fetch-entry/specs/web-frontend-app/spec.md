## ADDED Requirements

### Requirement: Dashboard full market data fetch entry point
The web frontend SHALL let users trigger a full market data fetch from the Dashboard through the shared frontend API client as a lower-priority market data operation than incremental fetch.

#### Scenario: User starts full market data fetch
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the full market data fetch action
- **THEN** the frontend sends `POST /api/market-data/fetch?mode=full` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate market data fetch submissions while the request is pending

#### Scenario: Full fetch entry point is lower priority than incremental fetch
- **WHEN** the Dashboard operation section renders market data fetch actions
- **THEN** the incremental fetch action is presented before the full fetch action
- **AND** the full fetch action is labeled for initialization or repair rather than as the default market data fetch action

#### Scenario: Dashboard reuses fetch result summary for full fetch
- **WHEN** the full market data fetch request returns a response
- **THEN** the Dashboard renders the existing market data fetch summary with fetched, inserted, updated, failed symbol, and error summary fields from the response

#### Scenario: Full fetch validation uses local API and SQLite
- **WHEN** frontend validation runs against a local FastAPI service configured with SQLite
- **THEN** the validation can trigger `POST /api/market-data/fetch?mode=full` through the shared frontend API client
- **AND** the response includes the status, requested ETF count, fetched row count, inserted row count, updated row count, failed symbols, and error summary fields that the Dashboard operation summary renders
- **AND** the validation does not rely only on frontend mock data

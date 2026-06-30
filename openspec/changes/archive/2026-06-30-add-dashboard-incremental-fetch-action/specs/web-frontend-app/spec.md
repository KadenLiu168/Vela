## ADDED Requirements

### Requirement: Dashboard incremental market data fetch action
The web frontend SHALL let users trigger an incremental market data fetch from the Dashboard through the shared frontend API client.

#### Scenario: User starts incremental market data fetch
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the market data fetch action
- **THEN** the frontend sends `POST /api/market-data/fetch?mode=incremental` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate submissions while the request is pending

#### Scenario: Dashboard refreshes after successful fetch
- **WHEN** the incremental market data fetch request succeeds
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed market data status is rendered from the latest Dashboard response

#### Scenario: Incremental fetch validation uses local API and SQLite
- **WHEN** frontend validation runs against a local FastAPI service configured with SQLite
- **THEN** the validation can trigger `POST /api/market-data/fetch?mode=incremental` through the shared frontend API client
- **AND** the backend persists the expected `DataFetchLog` and `MarketPrice` results through the existing market data fetch workflow
- **AND** the validation does not rely only on frontend mock data

## MODIFIED Requirements

### Requirement: Dashboard empty workflow states
The web frontend SHALL render Dashboard empty states for missing local market data, missing latest signal data, and missing recent backtest data that explain what local data is missing and the next local operation to run.

#### Scenario: Dashboard explains empty market data
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has zero price rows
- **THEN** the market data panel explains that no local market prices are stored
- **AND** it identifies fetching market data as the next local operation
- **AND** it does not mention login, accounts, users, deployment, hosting, or remote setup

#### Scenario: Dashboard explains empty signal data
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is null
- **THEN** the latest signal panel explains that no successful local signal exists
- **AND** it identifies generating a signal as the next local operation
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard explains empty backtest data
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is null
- **THEN** the recent backtest panel explains that no local backtest run exists
- **AND** it identifies running a backtest as the next local operation
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard renders empty API values without remote assumptions
- **WHEN** frontend validation renders the Dashboard route with zero market rows, no latest signal, and no recent backtest
- **THEN** the empty states identify local next operations through Dashboard action entry points
- **AND** the rendered copy does not rely on login, multi-user, or remote deployment assumptions

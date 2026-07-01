## ADDED Requirements

### Requirement: Backtest detail page loads persisted run detail
The web frontend SHALL render the Backtest Detail route from the real `GET /api/backtests/{run_id}` API response for the run id in the route.

#### Scenario: Backtest detail loads by route run id
- **WHEN** a developer opens `/backtests/8`
- **THEN** the Backtest Detail page requests `GET /api/backtests/8` through the shared frontend API client
- **AND** it renders values from the returned persisted backtest detail response

#### Scenario: Backtest detail shows run metadata
- **WHEN** the Backtest Detail API returns an existing run
- **THEN** the page shows the run id, strategy name, config version, date range, status, started timestamp, finished timestamp, and error message state

#### Scenario: Backtest detail shows parameter summary
- **WHEN** the Backtest Detail API returns `parameters_json`
- **THEN** the page shows a readable parameter summary derived from that API field

#### Scenario: Backtest detail shows metric summary
- **WHEN** the Backtest Detail API returns metric fields
- **THEN** the page shows total return, annualized return, maximum drawdown, volatility, and Sharpe ratio values from the response

### Requirement: Backtest detail page handles loading and missing runs
The web frontend SHALL render stable loading, missing-run, and API failure states for the Backtest Detail route.

#### Scenario: Backtest detail shows loading state
- **WHEN** the Backtest Detail route is waiting for the detail API response
- **THEN** the page shows a loading state without placeholder run data

#### Scenario: Backtest detail shows missing run state
- **WHEN** `GET /api/backtests/{run_id}` returns HTTP 404
- **THEN** the page shows a stable missing-run state for that run id

#### Scenario: Backtest detail shows API failure state
- **WHEN** the Backtest Detail API request fails for a non-404 HTTP error or network error
- **THEN** the page shows a concise API failure state

## MODIFIED Requirements

### Requirement: Frontend route placeholders
The web frontend SHALL provide client-side route areas for the Dashboard, Signal Detail, and Backtest Detail page areas.

#### Scenario: Dashboard route renders
- **WHEN** a developer opens the web frontend at `/`
- **THEN** the app renders the Dashboard page area

#### Scenario: Signal detail route renders
- **WHEN** a developer opens the web frontend at `/signals/demo-signal`
- **THEN** the app renders a Signal Detail page area for `demo-signal`

#### Scenario: Backtest detail route renders
- **WHEN** a developer opens the web frontend at `/backtests/1`
- **THEN** the app renders a Backtest Detail page area for run id `1`
- **AND** the page is backed by the Backtest Detail API instead of placeholder content

# web-frontend-app Specification

## Purpose
Define the minimal Vela web frontend application skeleton, development command, source layout, and validation expectations for future frontend work.
## Requirements
### Requirement: Web frontend application skeleton
The repository SHALL include an `apps/web` frontend application skeleton implemented with Vite, React, TypeScript, and npm.

#### Scenario: Web app directory exists
- **WHEN** a developer inspects the repository
- **THEN** `apps/web` contains the frontend package manifest, Vite entrypoint, TypeScript configuration, and React source entrypoint

### Requirement: Web development server command
The web frontend SHALL provide a documented development server command that can be run from the repository root as `npm --prefix apps/web run dev`.

#### Scenario: Developer starts the web dev server from the root
- **WHEN** a developer runs `npm --prefix apps/web run dev` from the repository root
- **THEN** the frontend development server starts using the `apps/web` package scripts

### Requirement: Extensible frontend source layout
The web frontend SHALL include directories for pages, components, API client code, and tests so later frontend issues can add behavior without reorganizing the app skeleton.

#### Scenario: Developer adds future frontend behavior
- **WHEN** a developer needs to add a page, reusable component, API client module, or frontend test
- **THEN** `apps/web/src` provides corresponding locations for that code

### Requirement: Web skeleton validation commands
The web frontend SHALL provide package scripts for type checking, linting, testing, and building the skeleton.

#### Scenario: Developer validates the frontend skeleton
- **WHEN** a developer runs the documented frontend validation commands
- **THEN** the commands complete against the `apps/web` skeleton without requiring backend services

### Requirement: Shared frontend API client
The web frontend SHALL provide a shared API client module that wraps API requests, parses JSON responses, and exposes endpoint helpers for frontend code.

#### Scenario: Frontend calls API through shared client
- **WHEN** frontend code needs the API health status
- **THEN** it calls a helper from the shared API client module instead of calling `fetch` directly from page or component code

### Requirement: Frontend API client success handling
The shared API client SHALL return parsed response data when the API returns a successful JSON response.

#### Scenario: Successful API response is parsed
- **WHEN** the API returns a 2xx JSON response
- **THEN** the client resolves with the parsed response body

### Requirement: Frontend API client HTTP error handling
The shared API client SHALL raise a normalized client error when the API returns a non-2xx HTTP response.

#### Scenario: HTTP error is normalized
- **WHEN** the API returns a non-2xx response
- **THEN** the client raises an error that identifies the failure as an HTTP error and includes the HTTP status

### Requirement: Frontend API client network error handling
The shared API client SHALL raise a normalized client error when the request fails before an HTTP response is available.

#### Scenario: Network error is normalized
- **WHEN** the browser request fails because the API cannot be reached
- **THEN** the client raises an error that identifies the failure as a network error

### Requirement: Local API integration validation
The web frontend SHALL provide a validation path that performs at least one real request against the local FastAPI service.

#### Scenario: Real local API request succeeds
- **WHEN** the local API service is running
- **THEN** the frontend validation path can call `GET /api/health` through the shared API client and receive the healthy status

### Requirement: Frontend route placeholders
The web frontend SHALL provide client-side route placeholders for the Dashboard, Signal Detail, and Backtest Detail page areas.

#### Scenario: Dashboard route renders
- **WHEN** a developer opens the web frontend at `/`
- **THEN** the app renders the Dashboard page area

#### Scenario: Signal detail route renders
- **WHEN** a developer opens the web frontend at `/signals/demo-signal`
- **THEN** the app renders a Signal Detail page placeholder for `demo-signal`

#### Scenario: Backtest detail route renders
- **WHEN** a developer opens the web frontend at `/backtests/demo-backtest`
- **THEN** the app renders a Backtest Detail page placeholder for `demo-backtest`

### Requirement: Local research workflow layout
The web frontend SHALL render a base layout for a local research workflow tool with navigation to Dashboard, Signal Detail, and Backtest Detail.

#### Scenario: First screen is the workflow dashboard
- **WHEN** a developer opens the default web frontend route
- **THEN** the first screen presents workflow dashboard content instead of marketing, login, or deployment content

#### Scenario: Navigation exposes research page areas
- **WHEN** a developer inspects the base layout navigation
- **THEN** it provides entries for Dashboard, Signal Detail, and Backtest Detail

### Requirement: Local-only frontend structure
The web frontend SHALL avoid login, multi-user, account management, and production deployment entry points in the base layout and route placeholders.

#### Scenario: Layout remains local-tool focused
- **WHEN** a developer inspects the rendered base layout and route placeholders
- **THEN** they do not include login, signup, account switching, team management, hosting, or production deployment actions

### Requirement: Dashboard aggregate page layout
The web frontend SHALL render the default Dashboard route as a local research workflow dashboard backed by the `GET /api/dashboard` aggregate contract.

#### Scenario: Dashboard aggregate sections render
- **WHEN** the Dashboard route receives a successful dashboard aggregate response
- **THEN** the first screen includes market data status, strategy summary, latest signal, recent backtest, and operation sections
- **AND** the sections use data from the dashboard aggregate response

#### Scenario: Dashboard supports empty workflow data
- **WHEN** the dashboard aggregate response has no latest signal or recent backtest
- **THEN** the Dashboard route renders explicit empty states for those sections without treating the response as a failure

#### Scenario: Dashboard API failure is visible
- **WHEN** the Dashboard route cannot load the dashboard aggregate response
- **THEN** the Dashboard route keeps the local workflow layout visible and shows a concise API failure state

### Requirement: Dashboard uses shared frontend API client
The web frontend SHALL call the dashboard aggregate endpoint through the shared API client module.

#### Scenario: Dashboard request uses shared endpoint helper
- **WHEN** the Dashboard route loads aggregate data
- **THEN** frontend page code uses a dashboard helper from `apps/web/src/api/client.ts` instead of calling `fetch` directly

### Requirement: Dashboard market data status states
The web frontend SHALL render the Dashboard market data status from the dashboard aggregate response with explicit populated and empty states.

#### Scenario: Dashboard shows populated market data status
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has one or more price rows
- **THEN** the market data panel shows the total price record count
- **AND** it shows the covered ETF count
- **AND** it shows the earliest trade date
- **AND** it shows the latest trade date

#### Scenario: Dashboard shows empty market data status
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has zero price rows
- **THEN** the market data panel shows a clear empty state indicating that no local market data has been stored yet
- **AND** it still shows zero price records and zero covered ETFs
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard market data status is backed by real aggregate API data
- **WHEN** dashboard validation exercises `GET /api/dashboard` against a local SQLite database with persisted market price rows
- **THEN** the returned market data status provides the same record count, ETF coverage, earliest trade date, and latest trade date that the Dashboard page renders
- **AND** the validation does not rely only on frontend mock data

### Requirement: Dashboard strategy configuration summary
The web frontend SHALL render the Dashboard strategy panel as a read-only summary of the current strategy configuration from the dashboard aggregate response.

#### Scenario: Dashboard shows current strategy configuration summary
- **WHEN** the Dashboard route receives a successful dashboard aggregate response containing strategy configuration fields
- **THEN** the strategy panel shows the strategy id and version
- **AND** it shows the configured momentum windows
- **AND** it shows the configured score weights
- **AND** it shows the configured Top N selection
- **AND** it shows the configured defensive asset
- **AND** it shows the configured transaction cost summary

#### Scenario: Dashboard strategy summary uses API data
- **WHEN** frontend validation renders the Dashboard route with a dashboard aggregate API response
- **THEN** the visible strategy configuration values come from the response strategy object
- **AND** the page code uses the shared dashboard API client helper instead of static configuration constants

#### Scenario: Dashboard strategy summary is read-only
- **WHEN** the Dashboard route renders the strategy configuration summary
- **THEN** it does not provide controls or links for editing strategy configuration

### Requirement: Dashboard latest signal summary states
The web frontend SHALL render the Dashboard latest signal panel from the dashboard aggregate response with populated and empty states.

#### Scenario: Dashboard shows latest successful signal summary
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is present
- **THEN** the signal panel shows the signal date
- **AND** it shows the signal result
- **AND** it shows the fallback status
- **AND** it shows the target holding count

#### Scenario: Dashboard shows empty latest signal state
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is null
- **THEN** the signal panel shows a clear empty state indicating that no successful signal has been generated yet
- **AND** it shows a generate-signal entry point
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard latest signal summary is backed by real API data
- **WHEN** dashboard validation exercises `GET /api/dashboard` against a local SQLite database with persisted strategy signal rows
- **THEN** the returned latest signal summary provides signal date, result, fallback status, and position count values that the Dashboard page renders
- **AND** the validation does not rely only on frontend mock data

### Requirement: Dashboard recent backtest summary states
The web frontend SHALL render the Dashboard recent backtest panel from the dashboard aggregate response with populated and empty states.

#### Scenario: Dashboard shows recent backtest summary
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is present
- **THEN** the backtest panel shows the backtest date range
- **AND** it shows the backtest status
- **AND** it shows total return, maximum drawdown, and Sharpe ratio summary values

#### Scenario: Dashboard shows empty recent backtest state
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is null
- **THEN** the backtest panel shows a clear empty state indicating that no backtest run has been recorded yet
- **AND** it shows a run-backtest entry point
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard recent backtest summary is backed by real API data
- **WHEN** dashboard validation exercises `GET /api/dashboard` against a local SQLite database with a persisted `BacktestRun` row
- **THEN** the returned recent backtest summary provides date range, status, total return, maximum drawdown, and Sharpe ratio values that the Dashboard page renders
- **AND** the validation does not rely only on frontend mock data

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

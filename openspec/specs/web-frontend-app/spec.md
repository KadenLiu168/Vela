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

### Requirement: Dashboard market data fetch result summary
The web frontend SHALL render a Dashboard operation summary from the real market data fetch API response after a fetch request completes.

#### Scenario: Dashboard shows successful fetch counts
- **WHEN** the Dashboard market data fetch request returns a `success` response
- **THEN** the operation summary shows fetched, inserted, and updated row counts from the response
- **AND** the summary does not show failed symbol guidance

#### Scenario: Dashboard shows partial fetch failures
- **WHEN** the Dashboard market data fetch request returns a `partial` response
- **THEN** the operation summary shows fetched, inserted, and updated row counts from the response
- **AND** it shows the failed symbols from the response
- **AND** it shows the response error summary when one is provided
- **AND** it guides the user to retry or check the data source or local data state

#### Scenario: Dashboard shows failed fetch details
- **WHEN** the Dashboard market data fetch request returns a `failed` response
- **THEN** the operation summary shows the failed symbols from the response
- **AND** it shows the response error summary when one is provided
- **AND** it guides the user to retry or check the data source or local data state

#### Scenario: Dashboard validates against real fetch response contract
- **WHEN** frontend validation calls the local API market data fetch endpoint through the shared client
- **THEN** the response includes the status, fetched row count, inserted row count, updated row count, failed symbols, and error summary fields that the Dashboard operation summary renders

### Requirement: Dashboard recent market data fetch log display
The web frontend SHALL render recent market data fetch log summaries from the dashboard aggregate response.

#### Scenario: Dashboard shows recent fetch log details
- **WHEN** the Dashboard route receives a successful dashboard aggregate response containing recent fetch log summaries
- **THEN** the Dashboard shows recent fetch time, mode, status, fetched row count, inserted row count, updated row count, and error summary for those records

#### Scenario: Dashboard shows empty fetch log history
- **WHEN** the Dashboard route receives a successful dashboard aggregate response with no recent fetch logs
- **THEN** the Dashboard shows a concise empty state for fetch history
- **AND** it does not treat the successful dashboard aggregate response as an API failure

### Requirement: Dashboard generate signal action
The web frontend SHALL let users trigger latest strategy signal generation from the Dashboard through the shared frontend API client.

#### Scenario: User starts signal generation
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the generate signal action
- **THEN** the frontend sends `POST /api/strategy-signals/generate` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate signal-generation submissions while the request is pending

#### Scenario: Dashboard refreshes after successful signal generation
- **WHEN** the generate signal request succeeds
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed latest signal summary is rendered from the latest Dashboard response

#### Scenario: Signal generation failure remains local to the operation
- **WHEN** the generate signal request fails
- **THEN** the Dashboard keeps the local workflow layout visible
- **AND** it shows a concise signal generation failure state
- **AND** it does not reload Dashboard aggregate data for the failed generation request

#### Scenario: Signal generation validation uses local API and SQLite
- **WHEN** frontend validation runs against a local FastAPI service configured with SQLite and sufficient market data
- **THEN** the validation can trigger `POST /api/strategy-signals/generate` through the shared frontend API client
- **AND** the backend persists the expected `StrategySignal` and `StrategySignalPosition` rows through the existing generation workflow
- **AND** the validation does not rely only on frontend mock data

### Requirement: Signal detail latest signal page
The web frontend SHALL render the Signal Detail page as a read-only latest strategy signal detail view backed by the structured latest signal API.

#### Scenario: Signal detail loads latest signal through shared client
- **WHEN** the Signal Detail route renders
- **THEN** frontend page code uses a latest signal helper from `apps/web/src/api/client.ts`
- **AND** the helper calls `GET /api/strategy-signals/latest`

#### Scenario: Signal detail shows latest signal metadata
- **WHEN** the latest signal API response has `has_signal: true`
- **THEN** the Signal Detail page shows the signal date
- **AND** it shows the config version
- **AND** it shows the result
- **AND** it shows the fallback status
- **AND** it shows the generated timestamp

#### Scenario: Signal detail shows target holdings table
- **WHEN** the latest signal API response has `has_signal: true` and includes positions
- **THEN** the Signal Detail page shows a target holdings table populated from the latest signal API `positions`
- **AND** the table shows each position's exchange, symbol, target weight, rank, score, and fallback status
- **AND** target weight is formatted as a clear percentage without losing meaningful decimal precision
- **AND** score is formatted as a readable decimal value without losing meaningful precision

#### Scenario: Signal detail shows empty target holdings state
- **WHEN** the latest signal API response has `has_signal: true` and includes no positions
- **THEN** the Signal Detail page shows a clear empty holdings state
- **AND** it does not treat the successful latest signal response as a request failure

#### Scenario: Signal detail shows empty latest signal state
- **WHEN** the latest signal API response has `has_signal: false`
- **THEN** the Signal Detail page shows a clear empty state explaining that no successful signal exists yet
- **AND** it does not treat the successful empty API response as a request failure

#### Scenario: Signal detail omits candidate diagnostics
- **WHEN** the Signal Detail page renders latest signal data
- **THEN** it does not show candidate ranking diagnostics

### Requirement: Dashboard latest signal backfill
The web frontend SHALL backfill the Dashboard latest signal summary from persisted latest signal data after a successful Dashboard signal-generation request.

#### Scenario: Dashboard refreshes aggregate and latest signal data after generation
- **WHEN** the Dashboard generate signal request succeeds
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** it loads latest signal data from `GET /api/strategy-signals/latest`
- **AND** it renders the latest signal summary from the refreshed persisted signal state

#### Scenario: Dashboard and Signal Detail show the same persisted latest signal
- **WHEN** signal generation succeeds and the latest signal endpoint returns the generated persisted signal
- **THEN** the Dashboard latest signal summary shows the same signal id, signal date, result, fallback status, and target holding count as the Signal Detail page can read from `GET /api/strategy-signals/latest`

#### Scenario: Dashboard can restore latest signal status after browser refresh
- **WHEN** the browser refreshes after a signal has been generated and persisted
- **THEN** the Dashboard loads backend data and renders the latest persisted signal summary without relying on in-memory generation result state

### Requirement: Dashboard run backtest action
The web frontend SHALL let users run a backtest from the Dashboard for an explicit date range through the shared frontend API client.

#### Scenario: User submits a valid backtest date range
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user enters `2026-01-01` as the start date and `2026-01-31` as the end date
- **AND** the user submits the run-backtest action
- **THEN** the frontend sends `POST /api/backtests/run?startDate=2026-01-01&endDate=2026-01-31` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate backtest submissions while the request is pending

#### Scenario: Dashboard validates backtest date format
- **WHEN** the user enters a start date or end date that is not a valid `YYYY-MM-DD` date
- **AND** the user submits the run-backtest action
- **THEN** the Dashboard shows a concise validation error
- **AND** no run-backtest API request is sent

#### Scenario: Dashboard validates backtest date ordering
- **WHEN** the user enters a start date later than the end date
- **AND** the user submits the run-backtest action
- **THEN** the Dashboard shows a concise validation error
- **AND** no run-backtest API request is sent

#### Scenario: Dashboard shows scoped backtest submission feedback
- **WHEN** the run-backtest API request succeeds
- **THEN** the Dashboard shows a scoped operation status indicating that the backtest run was submitted
- **AND** it does not add a backtest detail link
- **AND** it does not show the submitted run result summary
- **AND** it does not rely on mocked backtest results as the only validation path

#### Scenario: Run backtest validation uses local API and SQLite
- **WHEN** frontend validation runs against a local FastAPI service configured with SQLite and sufficient market data
- **THEN** the validation can trigger `POST /api/backtests/run` through the shared frontend API client
- **AND** the backend persists the expected `BacktestRun` and `BacktestEquityCurve` rows through the existing backtest workflow
- **AND** the validation does not rely only on frontend mock data

### Requirement: Dashboard backtest run result summary
The web frontend SHALL render the result returned by the run backtest API after a successful Dashboard backtest submission.

#### Scenario: Dashboard shows successful backtest run summary
- **WHEN** a user submits a valid Dashboard backtest date range
- **AND** `POST /api/backtests/run` returns a successful JSON response
- **THEN** the Operations panel shows the returned run id
- **AND** it shows the returned status
- **AND** it shows the returned trading day count
- **AND** it shows the returned signal count
- **AND** it shows core metric summary values from the response

#### Scenario: Dashboard links to backtest detail after successful run
- **WHEN** the Dashboard renders a successful backtest run summary
- **THEN** the summary provides an entry point to `/backtests/<run id>`

#### Scenario: Dashboard shows operation error for failed backtest run
- **WHEN** a valid Dashboard backtest submission fails with an HTTP or network error
- **THEN** the Operations panel shows a concise operation-level backtest error summary
- **AND** it does not render a successful run summary

#### Scenario: Backtest run validation uses real API response shape
- **WHEN** frontend validation exercises the run backtest client against a local FastAPI service
- **THEN** the response includes run id, status, trading day count, signal count, and core metric fields that the Dashboard summary renders
- **AND** the validation does not rely only on frontend mock data

### Requirement: Dashboard recent backtest refresh
The web frontend SHALL refresh the Dashboard recent backtest summary from the backend Dashboard API after a successful Dashboard backtest submission.

#### Scenario: Successful backtest refreshes recent summary
- **WHEN** a user submits a valid Dashboard backtest date range
- **AND** `POST /api/backtests/run` succeeds
- **THEN** the frontend requests the Dashboard aggregate from `GET /api/dashboard`
- **AND** the Recent backtest panel renders the backend-persisted recent backtest summary returned by that Dashboard aggregate
- **AND** the Operations panel continues to render the immediate run response summary

#### Scenario: Browser refresh restores recent backtest summary
- **WHEN** the Dashboard route loads after a browser refresh
- **AND** `GET /api/dashboard` returns a persisted recent backtest summary
- **THEN** the Recent backtest panel renders that persisted summary without requiring another run-backtest action

#### Scenario: Failed backtest does not refresh recent summary
- **WHEN** a valid Dashboard backtest submission fails with an HTTP or network error
- **THEN** the Operations panel shows a concise operation-level backtest error summary
- **AND** the frontend does not issue an additional Dashboard aggregate refresh for that failed run
- **AND** it does not render a stale successful run response summary

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

### Requirement: Backtest detail metric cards
The web frontend SHALL render core performance metrics on the Backtest Detail page as metric cards sourced from the `GET /api/backtests/{run_id}` response.

#### Scenario: Backtest detail shows populated metric cards
- **WHEN** the Backtest Detail API returns total return, annualized return, maximum drawdown, volatility, and Sharpe ratio values for an existing run
- **THEN** the Backtest Detail page shows a metric card for each returned metric
- **AND** total return, annualized return, maximum drawdown, and volatility are formatted as percentages
- **AND** Sharpe ratio is formatted as a decimal value

#### Scenario: Backtest detail metric cards show null state
- **WHEN** the Backtest Detail API returns null for any core metric field
- **THEN** the corresponding metric card shows `n/a`
- **AND** the page does not treat the successful API response as an error

#### Scenario: Backtest detail metric cards use real API data
- **WHEN** frontend validation renders the Backtest Detail route with a successful detail API response
- **THEN** the visible metric card values come from the response metrics object
- **AND** the page code uses the shared backtest detail API client helper instead of static metric data

### Requirement: Backtest detail equity curve chart
The web frontend SHALL render a net value equity curve on the Backtest Detail page from the `GET /api/backtests/{run_id}` response.

#### Scenario: Backtest detail shows net value line chart
- **WHEN** the Backtest Detail API returns two or more equity curve rows with trade dates and finite net values
- **THEN** the Backtest Detail page renders a line chart using those `trade_date` and `net_value` values
- **AND** the chart is labeled as the equity curve

#### Scenario: Backtest detail handles empty equity curve
- **WHEN** the Backtest Detail API returns no valid equity curve points
- **THEN** the Backtest Detail page shows a clear empty equity curve state
- **AND** the page does not treat the successful API response as an error

#### Scenario: Backtest detail handles single equity curve point
- **WHEN** the Backtest Detail API returns exactly one valid equity curve point
- **THEN** the Backtest Detail page shows the single trade date and net value as a limited curve state
- **AND** the page does not draw a multi-point line chart

#### Scenario: Backtest detail limits first chart scope
- **WHEN** the Backtest Detail page renders equity curve data
- **THEN** it does not render a drawdown curve, monthly returns chart, or return distribution chart


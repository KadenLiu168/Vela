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
The web frontend SHALL provide package scripts for type checking, linting, testing, and building the skeleton. Type checking and production build validation MUST complete without requiring backend services, local mock services, or API integration test setup.

#### Scenario: Developer validates the frontend skeleton
- **WHEN** a developer runs the documented frontend validation commands
- **THEN** the commands complete against the `apps/web` skeleton without requiring backend services

#### Scenario: Developer validates the production frontend build
- **WHEN** a developer runs `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` from the repository root
- **THEN** TypeScript validation and the production build complete successfully
- **AND** the commands do not require a running local API service, seeded SQLite data, or frontend mock service

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

### Requirement: Backtest detail equity curve ember highlights
The web frontend SHALL render restrained Ember Orange highlight points on Backtest Detail equity curve charts that contain two or more valid points, while retaining the Brass equity curve line.

#### Scenario: Multi-point equity curve shows ember highlight points
- **WHEN** the Backtest Detail API returns two or more valid equity curve rows with finite net values
- **THEN** the Backtest Detail page renders the existing equity curve line using `data-testid="equity-curve-line"`
- **AND** it renders small Ember Orange circle highlights for selected end or extreme points
- **AND** the highlights do not replace the Brass equity curve line

#### Scenario: Empty equity curve does not render highlights
- **WHEN** the Backtest Detail API returns no valid equity curve rows
- **THEN** the Backtest Detail page renders the empty equity curve state
- **AND** it does not render the equity curve line
- **AND** it does not render Ember Orange chart highlight points

#### Scenario: Single-point equity curve does not render chart highlights
- **WHEN** the Backtest Detail API returns exactly one valid equity curve row
- **THEN** the Backtest Detail page renders the single-point equity curve state
- **AND** it does not render the equity curve line
- **AND** it does not render Ember Orange chart highlight points

### Requirement: Backtest detail equity curve summary
The web frontend SHALL render a basic equity curve summary on the Backtest Detail page from valid `equity_curve` rows returned by `GET /api/backtests/{run_id}`.

#### Scenario: Backtest detail shows multi-point equity curve summary
- **WHEN** the Backtest Detail API returns two or more equity curve rows with finite net values
- **THEN** the Backtest Detail page shows the valid equity curve point count
- **AND** it shows the first valid trade date and net value
- **AND** it shows the last valid trade date and net value
- **AND** it shows the minimum and maximum valid net values

#### Scenario: Backtest detail shows single-point equity curve summary
- **WHEN** the Backtest Detail API returns exactly one valid equity curve point
- **THEN** the Backtest Detail page shows the valid equity curve point count
- **AND** it shows the point trade date and net value
- **AND** it does not draw a multi-point line chart

#### Scenario: Backtest detail summary uses real detail API data
- **WHEN** frontend validation renders the Backtest Detail route with a successful detail API response
- **THEN** the visible equity curve summary values come from the response `equity_curve` rows
- **AND** the page code uses the shared backtest detail API client helper instead of static curve summary data

### Requirement: Shared frontend value formatting
The web frontend SHALL centralize reusable formatting for displayed numbers, dates, percentages, Decimal strings, and nullable values instead of duplicating page-local implementations.

#### Scenario: Pages reuse shared formatters
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders API-provided numeric, date, percentage, Decimal string, or nullable values
- **THEN** page code uses shared frontend formatter helpers for those value displays
- **AND** page-local formatting helpers are limited to page-specific composition that calls the shared helpers

### Requirement: Consistent research value display
The web frontend SHALL display backtest metrics, target weights, scores, dates, and nullable values consistently across research workflow pages.

#### Scenario: Backtest metric percentages are formatted consistently
- **WHEN** Dashboard or Backtest Detail renders total return, annualized return, maximum drawdown, or volatility from Decimal ratio strings
- **THEN** each finite value is displayed as a percentage with two fractional digits
- **AND** each null metric is displayed as `n/a`

#### Scenario: Signal target weights and scores are formatted consistently
- **WHEN** Signal Detail renders target holding rows from Decimal string values
- **THEN** target weights are displayed as percentages without unnecessary trailing zeroes
- **AND** scores are displayed as decimal values without unnecessary trailing zeroes
- **AND** null rank or score values are displayed as `n/a`

#### Scenario: Dates and nullable metadata are explicit
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders API-provided date fields or nullable metadata
- **THEN** date values are displayed in a consistent `YYYY-MM-DD` form when the API value is an ISO date or timestamp string
- **AND** nullable metadata values are displayed as `n/a` when absent

### Requirement: Frontend page loading feedback
The web frontend SHALL render a consistent page-loading feedback state while Dashboard, Signal Detail, or Backtest Detail data requests are pending.

#### Scenario: Dashboard shows page loading feedback
- **WHEN** the Dashboard route is waiting for `GET /api/dashboard`
- **THEN** the page shows a clear loading feedback state without placeholder successful data

#### Scenario: Signal detail shows page loading feedback
- **WHEN** the Signal Detail route is waiting for `GET /api/strategy-signals/latest`
- **THEN** the page shows a clear loading feedback state without placeholder signal data

#### Scenario: Backtest detail shows page loading feedback
- **WHEN** the Backtest Detail route is waiting for `GET /api/backtests/{run_id}`
- **THEN** the page shows a clear loading feedback state without placeholder run data

### Requirement: Dashboard operation feedback and concurrency protection
The web frontend SHALL render explicit Dashboard operation feedback for market data fetch, signal generation, and backtest run operations, and MUST prevent duplicate or conflicting Dashboard operations while any one of those operations is pending.

#### Scenario: Market data fetch shows pending and completion feedback
- **WHEN** a user starts an incremental or full market data fetch
- **THEN** the Dashboard shows an in-progress feedback state for the active fetch
- **AND** duplicate market data fetch submissions are prevented while the fetch is pending
- **AND** signal generation and backtest run submissions are disabled while the fetch is pending
- **AND** the Operations panel shows success or failure feedback after the fetch completes

#### Scenario: Signal generation shows pending and completion feedback
- **WHEN** a user starts signal generation
- **THEN** the Dashboard shows an in-progress feedback state for signal generation
- **AND** duplicate signal-generation submissions are prevented while generation is pending
- **AND** market data fetch and backtest run submissions are disabled while generation is pending
- **AND** the Operations panel shows success or failure feedback after generation completes

#### Scenario: Backtest run shows pending and completion feedback
- **WHEN** a user submits a valid backtest date range
- **THEN** the Dashboard shows an in-progress feedback state for the backtest run
- **AND** duplicate backtest submissions are prevented while the run is pending
- **AND** market data fetch and signal generation submissions are disabled while the run is pending
- **AND** the Operations panel shows success or failure feedback after the run completes

### Requirement: Dashboard operation error summaries
The web frontend SHALL render user-understandable operation-level error summaries when Dashboard market data fetch, signal generation, or backtest run requests fail.

#### Scenario: Market data fetch request failure shows reason and next step
- **WHEN** the Dashboard market data fetch request fails with an API error response
- **THEN** the Operations panel shows that the market data fetch failed
- **AND** it shows a readable reason from the API error response when one is available
- **AND** it shows guidance to retry after checking data source availability and local ETF/data state
- **AND** the API error response text is not the only visible failure guidance

#### Scenario: Signal generation request failure shows reason and next step
- **WHEN** the Dashboard signal generation request fails with an API error response
- **THEN** the Operations panel shows that signal generation failed
- **AND** it shows a readable reason from the API error response when one is available
- **AND** it shows guidance to fetch market data or review local strategy configuration before retrying
- **AND** the API error response text is not the only visible failure guidance

#### Scenario: Backtest run request failure shows reason and next step
- **WHEN** the Dashboard run-backtest request fails with an API error response
- **THEN** the Operations panel shows that the backtest run failed
- **AND** it shows a readable reason from the API error response when one is available
- **AND** it shows guidance to verify the date range and available local market data or signals before retrying
- **AND** the API error response text is not the only visible failure guidance

#### Scenario: Operation error summaries avoid raw technical text as sole guidance
- **WHEN** an operation request fails with a technical API error detail such as a database exception or stack-like text
- **THEN** the Operations panel still shows operation-specific next-step guidance
- **AND** it does not rely on the raw technical detail as the only visible user prompt

### Requirement: Frontend API error category mapping
The shared frontend API client SHALL parse stable API error envelopes and expose a readable error category for frontend code.

#### Scenario: Validation error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `validation`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `validation`
- **AND** the error message is the readable API error message

#### Scenario: Not found error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `not_found`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `not_found`
- **AND** the HTTP status remains available to page code

#### Scenario: Operation failed error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `operation_failed`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `operation_failed`
- **AND** Dashboard operation feedback can render the readable reason

#### Scenario: Unexpected error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `unexpected`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `unexpected`
- **AND** the frontend can show a generic readable failure state

### Requirement: Frontend real API error validation
The web frontend SHALL include validation for stable API error mapping that can run against real backend error responses.

#### Scenario: Local API error validation uses backend response shape
- **WHEN** frontend validation receives a stable error response produced by the local API error contract
- **THEN** the shared API client maps the response category and message without depending only on legacy `detail` strings

### Requirement: Dashboard first-run guidance
The web frontend SHALL render lightweight, non-blocking first-run guidance on the Dashboard when local setup data is missing or unavailable.

#### Scenario: Dashboard guides empty local market data setup
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has zero price rows
- **THEN** the Dashboard shows a first-run guidance surface that identifies fetching local market data as the next setup step
- **AND** existing Dashboard operation buttons remain available for direct use
- **AND** the guidance does not mention login, accounts, users, teams, hosting, deployment, production, or remote setup

#### Scenario: Dashboard guides local database initialization after load failure
- **WHEN** the Dashboard route cannot load the dashboard aggregate response
- **THEN** the Dashboard keeps the local workflow layout visible
- **AND** it shows first-run guidance that identifies initializing the local database before fetching market data as the next setup step
- **AND** existing Dashboard operation buttons remain visible for direct use
- **AND** the guidance does not mention login, accounts, users, teams, hosting, deployment, production, or remote setup

#### Scenario: Dashboard hides first-run guidance after setup data exists
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has one or more price rows
- **THEN** the Dashboard does not show the first-run guidance surface
- **AND** the regular workflow panels and operation controls remain visible

### Requirement: Dashboard refresh and empty state refinement
The web frontend SHALL let users manually refresh Dashboard status, SHALL preserve successful operation feedback when a follow-up Dashboard refresh fails, and SHALL align Dashboard empty-state copy with the next local Dashboard action.

#### Scenario: User manually refreshes Dashboard status
- **WHEN** the Dashboard route has rendered
- **AND** the user triggers the manual Dashboard refresh action
- **THEN** the frontend reloads Dashboard status from `GET /api/dashboard` through the shared frontend API client
- **AND** the refreshed Dashboard values are rendered from the latest Dashboard response

#### Scenario: Operation success remains visible when Dashboard refresh fails
- **WHEN** a Dashboard market data fetch, signal generation, or backtest run request succeeds
- **AND** the follow-up Dashboard status refresh fails with an HTTP or network error
- **THEN** the Operations panel keeps the successful operation summary visible
- **AND** the Dashboard shows the refresh failure as a Dashboard status problem instead of replacing the operation summary with an operation failure

#### Scenario: Empty states point to matching Dashboard actions
- **WHEN** the Dashboard route receives a successful dashboard aggregate response with missing local market data, latest signal data, or recent backtest data
- **THEN** each empty state identifies the matching local Dashboard action or Operations panel control needed next
- **AND** the rendered copy does not rely on login, multi-user, remote deployment, hosting, or production assumptions

### Requirement: Key frontend component regions have controlled fixture coverage
The web frontend SHALL validate critical local workflow component regions with controlled fixtures that match the real API response field names and nesting.

#### Scenario: Dashboard status blocks are covered
- **WHEN** frontend tests render the Dashboard route with a successful dashboard aggregate fixture
- **THEN** the tests MUST verify the Dashboard market data status block renders price rows, covered ETFs, trade-date boundaries, latest signal status, and recent backtest metric summary values from that fixture

#### Scenario: Target holdings table is covered
- **WHEN** frontend tests render the Signal Detail route with a successful latest-signal fixture containing positions
- **THEN** the tests MUST verify the target holdings table renders exchange, symbol, target weight, rank, score, and fallback fields from the fixture

#### Scenario: Backtest metric cards are covered
- **WHEN** frontend tests render the Backtest Detail route with a successful backtest detail fixture
- **THEN** the tests MUST verify the backtest metric cards render total return, annualized return, max drawdown, volatility, and Sharpe ratio fields from the fixture

#### Scenario: Error summaries are covered
- **WHEN** frontend tests trigger Dashboard operation failures or page-level API failures
- **THEN** the tests MUST verify concise user-visible error summaries render the failure type, reason, and next-step or API-unavailable message

### Requirement: Key frontend component states are covered
The web frontend SHALL validate loading, empty, and error states for key local workflow component regions.

#### Scenario: Loading states are covered
- **WHEN** frontend tests render Dashboard, Signal Detail, or Backtest Detail while the corresponding API request is pending
- **THEN** the tests MUST verify the relevant loading state is visible without rendering stale fixture data

#### Scenario: Empty states are covered
- **WHEN** frontend tests render successful API responses with missing local workflow data
- **THEN** the tests MUST verify empty states for missing Dashboard data, missing target holdings, and missing backtest detail chart data without treating the responses as failures

#### Scenario: Error states are covered
- **WHEN** frontend tests render rejected API requests or failed Dashboard operations
- **THEN** the tests MUST verify user-visible error states remain scoped to the affected page or operation region

### Requirement: Dashboard persisted detail entry points
The web frontend SHALL provide detail entry points from populated persisted Dashboard summaries after Dashboard data is loaded or refreshed.

#### Scenario: Dashboard latest signal summary links to signal detail
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is present
- **THEN** the latest signal panel provides a detail entry point to the Signal Detail route
- **AND** the entry point remains available after a browser refresh that reloads persisted backend data

#### Scenario: Dashboard recent backtest summary links to backtest detail
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is present
- **THEN** the recent backtest panel provides a detail entry point to `/backtests/<run id>`
- **AND** the entry point remains available after a browser refresh that reloads persisted backend data

### Requirement: Browser manual acceptance checklist
The web frontend SHALL provide a browser manual acceptance checklist for local validation and regression of the Phase 1 frontend workflow.

#### Scenario: Checklist covers primary workflow areas
- **WHEN** a developer opens the browser manual acceptance checklist
- **THEN** it covers Dashboard, market data fetch, signal generation, backtest execution, Signal Detail, and Backtest Detail validation areas

#### Scenario: Checklist covers key UI states
- **WHEN** a developer follows the browser manual acceptance checklist
- **THEN** it includes empty-state, error-state, and success-state checks for the relevant frontend workflow areas

#### Scenario: Checklist identifies backend data requirements
- **WHEN** a checklist step requires a running local API service, seeded SQLite data, or workflow-generated backend records
- **THEN** the checklist explicitly marks that backend data requirement

### Requirement: Web global design token foundation
The web frontend SHALL expose the provided design token foundation through CSS custom properties in `apps/web/src/styles.css`, covering core colors, typography, spacing, layout, radius, and surface tokens from the project design reference.

#### Scenario: Global stylesheet defines design tokens
- **WHEN** a developer inspects `apps/web/src/styles.css`
- **THEN** the stylesheet defines CSS custom properties for the provided core colors, font families, type scale, spacing scale, layout values, border radii, and surface values
- **AND** those properties are available from the global `:root` scope

#### Scenario: Base page styles use design tokens
- **WHEN** the web frontend renders any route
- **THEN** the base document typography, text color, and page background are driven by the global design token custom properties
- **AND** the rendered route structure, API calls, and business behavior remain unchanged

#### Scenario: Token wiring avoids new build dependencies
- **WHEN** a developer validates the frontend package
- **THEN** the design token foundation is available without adding a token build pipeline, UI framework, or new runtime dependency

### Requirement: App Shell editorial header navigation
The web frontend SHALL render the App Shell header and navigation with the tokenized editorial visual system while preserving existing navigation semantics and behavior.

#### Scenario: Header uses editorial visual tokens
- **WHEN** a developer inspects the App Shell header implementation and stylesheet
- **THEN** the brand, API metadata, navigation container, and navigation links use dedicated styling hooks
- **AND** their visual styles use the global design token custom properties for typography, neutral colors, spacing, radius, and surfaces

#### Scenario: Navigation remains behaviorally unchanged
- **WHEN** a user activates an App Shell navigation link
- **THEN** the existing client-side navigation behavior is used
- **AND** the link labels, href targets, and active `aria-current="page"` semantics remain unchanged

#### Scenario: Navigation renders as a responsive pill group
- **WHEN** the App Shell renders on desktop or narrow viewport widths
- **THEN** the navigation appears as a warm-gray pill-style group with text-style nav items
- **AND** the group remains readable and can wrap without introducing new routes, dropdowns, or controls

### Requirement: Dashboard data observatory card styling
The web frontend SHALL render the Dashboard overview cards and workflow grid using the flat editorial data observatory visual language defined by `DESIGN.md`.

#### Scenario: Dashboard cards use editorial surfaces
- **WHEN** the Dashboard route renders its overview grid
- **THEN** the grid and panels use the existing Ash, Fog, Canvas, and Mist surface tokens for backgrounds and borders
- **AND** the cards do not use box shadows or blue admin-dashboard surfaces

#### Scenario: Dashboard data hierarchy uses design text colors
- **WHEN** the Dashboard route renders panel headings, metrics, compact details, and empty states
- **THEN** headings and primary values use Graphite
- **AND** body/data text uses Steel
- **AND** metadata labels use Slate

#### Scenario: Dashboard responsive readability is preserved
- **WHEN** the Dashboard route is viewed at desktop and mobile widths
- **THEN** the overview grid remains readable without changing the Dashboard information architecture, DOM semantics, API usage, routes, data loading, or operation behavior

### Requirement: Dashboard action and feedback styling follows design tokens
The web frontend SHALL render Dashboard operation actions, empty-state action buttons, Backtest run form controls, load states, alerts, operation summaries, operation guidance, and operation links using the project design-token visual language.

#### Scenario: Dashboard actions use Graphite action dialects
- **WHEN** the Dashboard renders operation buttons, empty-state action buttons, and the refresh action
- **THEN** the actions use 0px button radius
- **AND** filled actions use Graphite backgrounds instead of Ember Orange backgrounds
- **AND** outlined actions use tokenized Graphite, Mist, Canvas, Fog, and typography values

#### Scenario: Backtest form controls use tokens
- **WHEN** the Dashboard renders the Backtest run date inputs
- **THEN** the controls use tokenized border, background, color, typography, spacing, and 0px control radius values

#### Scenario: Operation feedback avoids broad chromatic blocks
- **WHEN** Dashboard loading, error, success, partial, failed, and validation feedback is visible
- **THEN** the feedback uses neutral tokenized surfaces and borders with narrow Ember or Brass accents
- **AND** broad blue, green, or red filled feedback blocks are not used

#### Scenario: Dashboard operation behavior is preserved
- **WHEN** Dashboard operation buttons, Backtest validation feedback, loading feedback, error feedback, and operation summaries render
- **THEN** existing button enabled, disabled, and loading conditions remain unchanged
- **AND** existing API calls, routing targets, form validation logic, and `role="status"` or `role="alert"` accessibility semantics remain unchanged

### Requirement: Signal Detail editorial metadata and holdings table styling
The web frontend SHALL render the Signal Detail metadata and Target holdings table using the flat editorial data product visual language defined by `DESIGN.md` while preserving existing Signal Detail behavior.

#### Scenario: Signal metadata uses editorial token hierarchy
- **WHEN** the Signal Detail page renders latest signal metadata
- **THEN** the metadata block uses existing tokenized neutral surfaces, borders, spacing, and typography
- **AND** metadata labels use Slate
- **AND** metadata values use Graphite or Steel for readable data hierarchy

#### Scenario: Target holdings table uses restrained editorial styling
- **WHEN** the Signal Detail page renders target holdings
- **THEN** the table container, header, row dividers, and cells use existing Graphite, Steel, Slate, Mist, Fog, Ash, Canvas, spacing, typography, and radius tokens
- **AND** target weight, rank, and score columns are visually readable as numeric data
- **AND** the table does not introduce default blue admin-dashboard styling, box shadows, sorting, filtering, or pagination

#### Scenario: Target holdings horizontal scrolling remains available
- **WHEN** the Signal Detail page is viewed on a narrow viewport
- **THEN** the Target holdings table remains horizontally scrollable when needed
- **AND** existing Signal Detail API calls, route structure, signal API helper usage, and positions rendering data remain unchanged

#### Scenario: Signal Detail empty states remain visually consistent
- **WHEN** the Signal Detail page renders either the no-signal state or the no-target-holdings state
- **THEN** the empty state uses the shared tokenized editorial empty-state styling
- **AND** it does not treat successful empty API responses as request failures

### Requirement: Backtest Detail data dashboard card styling
The web frontend SHALL render the Backtest Detail metrics, equity curve, and parameters areas using the flat editorial data dashboard card visual language defined by `DESIGN.md` while preserving existing Backtest Detail behavior.

#### Scenario: Backtest metrics use editorial data cards
- **WHEN** the Backtest Detail route renders a successful backtest detail response
- **THEN** the metric card grid and metric cards MUST use tokenized neutral surfaces, borders, spacing, radii, and typography consistent with the data dashboard card system
- **AND** the rendered metric labels and formatted values remain unchanged

#### Scenario: Equity curve uses warm chart accent
- **WHEN** the Backtest Detail route renders a multi-point equity curve
- **THEN** the hand-written SVG chart remains present with `data-testid="equity-curve-line"`
- **AND** the equity curve stroke MUST use the `DESIGN.md` Ember or Brass accent token instead of a blue chart stroke
- **AND** the equity curve path calculation, API data usage, and chart summary values remain unchanged

#### Scenario: Equity curve empty and single-point states remain readable
- **WHEN** the Backtest Detail route renders no valid equity curve points or exactly one valid equity curve point
- **THEN** the existing empty or single-point message remains visible
- **AND** the surrounding surface, spacing, and summary details remain readable using tokenized Backtest Detail styling

#### Scenario: Parameters use readable tokenized surface
- **WHEN** the Backtest Detail route renders run parameters
- **THEN** the parameters block remains preformatted and horizontally scrollable when needed
- **AND** it uses tokenized neutral surfaces, borders, radius, typography, and spacing consistent with the surrounding Backtest Detail cards

### Requirement: Shared frontend status presentation
The web frontend SHALL render shared loading, error, info, success, and empty-state feedback across Dashboard, Signal Detail, and Backtest Detail using tokenized neutral surfaces, borders, typography, spacing, and narrow state accents.

#### Scenario: Shared feedback variants preserve semantics
- **WHEN** loading, info, success, or error `FeedbackMessage` variants render
- **THEN** non-error variants MUST keep `role="status"`
- **AND** error variants MUST keep `role="alert"`
- **AND** each variant MUST use the shared `feedback-message` class plus a variant-specific class

#### Scenario: Empty states use shared tokenized presentation
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders an existing empty-state message
- **THEN** the message uses the shared `.empty-state` tokenized editorial presentation
- **AND** successful empty API responses are not treated as request failures

#### Scenario: Detail and dashboard states avoid broad chromatic blocks
- **WHEN** Dashboard load states, page loading feedback, page error feedback, operation feedback, or empty states are visible
- **THEN** the visible state presentation uses neutral project tokens with narrow Ember, Brass, Graphite, Slate, or Mist accents
- **AND** broad blue, green, or red filled feedback blocks are not used
- **AND** existing API calls, route targets, loading timing, error categorization, and message meaning remain unchanged

### Requirement: Frontend visual consistency QA
The web frontend SHALL keep the Dashboard, Signal Detail, Backtest Detail, AppShell navigation, tables, cards, forms, buttons, and feedback states visually aligned with `DESIGN.md`.

#### Scenario: Required frontend routes pass visual QA
- **WHEN** a developer inspects `/`, `/signals/demo-signal`, and `/backtests/1`
- **THEN** the visible UI uses the established graphite, canvas, ash, fog, ivory, ember, and brass design tokens instead of a blue or green default admin palette
- **AND** buttons, cards, tables, forms, navigation, and feedback states use consistent tokenized radius, typography, spacing, and surface treatments

#### Scenario: Required frontend routes remain readable on mobile
- **WHEN** a developer inspects `/`, `/signals/demo-signal`, and `/backtests/1` in a mobile viewport
- **THEN** the page header, navigation, action controls, content cards, forms, tables, and feedback states do not visibly overlap, clip, or become unreadable

#### Scenario: Visual QA does not change application behavior
- **WHEN** the frontend visual QA pass is implemented
- **THEN** existing business logic, API calls, and route structure remain unchanged
- **AND** the frontend does not add a large UI framework or new production dependency

### Requirement: Web frontend font loading baseline
The web frontend SHALL load Inter for body and UI text and SHALL provide a non-system PolySans substitute for heading, navigation, and button typography until licensed PolySans assets are self-hosted.

#### Scenario: Frontend document loads configured web fonts
- **WHEN** a developer inspects the web frontend HTML entrypoint
- **THEN** it includes a font loading source for Inter weights used by the CSS tokens
- **AND** it includes a font loading source for the configured PolySans substitute
- **AND** the font loading source uses a swap strategy so text does not remain invisible while fonts load

#### Scenario: PolySans stack preserves future self-hosting priority
- **WHEN** a developer inspects `apps/web/src/styles.css :root`
- **THEN** `--font-polysans` keeps `"PolySans"` before the substitute family
- **AND** it includes the current substitute before system font fallbacks

#### Scenario: Body text uses Inter stack
- **WHEN** a developer inspects the global web frontend CSS
- **THEN** body and root typography use `--font-inter`
- **AND** `--font-inter` includes `"Inter"` before system font fallbacks

### Requirement: Web frontend token source documentation
The repository SHALL document that `apps/web/src/styles.css :root` is the current web frontend implementation token source, while `tokens.json` and `variables.css` are design references that do not directly drive the build.

#### Scenario: Implementation token source is marked
- **WHEN** a developer inspects `apps/web/src/styles.css :root`
- **THEN** the file identifies the root custom properties as the current implementation token source

#### Scenario: Reference token artifacts are marked
- **WHEN** a developer inspects the design token reference documentation or root CSS reference file
- **THEN** it states that `tokens.json` and `variables.css` are design references
- **AND** it states that they are not direct build inputs for the web frontend

#### Scenario: Token documentation records implementation-only additions
- **WHEN** a developer inspects the token source documentation
- **THEN** it records any current token values in `apps/web/src/styles.css :root` that are implementation additions beyond the DESIGN.md reference scale

### Requirement: Editorial research page hierarchy
The web frontend SHALL render the Dashboard, Signal Detail, and Backtest Detail page skeletons with editorial spacing, clear page-heading hierarchy, and a restrained asymmetric featured card using the existing design tokens.

#### Scenario: Research pages use editorial spacing tokens
- **WHEN** a developer inspects the active web stylesheet for the Dashboard, Signal Detail, and Backtest Detail page skeletons
- **THEN** page-level section spacing uses the existing `--section-gap` token
- **AND** prominent page or card containers use the existing `--card-padding` token

#### Scenario: Page headings have clear hierarchy
- **WHEN** a user opens the Dashboard, Signal Detail, or Backtest Detail page
- **THEN** the page heading presents an eyebrow followed by the page title
- **AND** the page title uses either `--text-heading-lg` or `--text-display`
- **AND** the title font weight remains 400

#### Scenario: Dashboard remains an internal research tool
- **WHEN** a user opens the Dashboard route
- **THEN** the first screen remains focused on local workflow status and data panels
- **AND** it does not introduce marketing hero copy, decorative hero artwork, or CTA button clusters

#### Scenario: Signature asymmetric card is restrained
- **WHEN** a developer inspects the active web stylesheet
- **THEN** at least one featured guidance block uses `--radius-asymmetric-card`
- **AND** ordinary dashboard data panels do not use the asymmetric radius

#### Scenario: Mobile page skeleton remains usable
- **WHEN** the viewport is below 720px wide
- **THEN** the Dashboard, Signal Detail, and Backtest Detail page skeletons continue to stack content without horizontal layout regression from editorial spacing or card padding

### Requirement: Web frontend keyboard focus visibility
The web frontend SHALL provide a clear visible focus indicator for keyboard-focused interactive controls, including links, buttons, navigation entries, and form inputs.

#### Scenario: Keyboard focus is visible on interactive controls
- **WHEN** a user tabs through Dashboard, Signal Detail, and Backtest Detail controls
- **THEN** each focused link, button, navigation entry, and input shows a clear focus ring
- **AND** the focus ring uses outline-based styling instead of box-shadow-based styling

#### Scenario: Focus styling preserves disabled control semantics
- **WHEN** an action button or form control is disabled
- **THEN** the control remains visibly disabled
- **AND** the frontend does not add hover or focus affordances that imply the disabled control is actionable

### Requirement: Web frontend restrained interaction motion
The web frontend SHALL keep hover and transition feedback restrained and SHALL respect reduced-motion user preferences.

#### Scenario: Hover feedback does not shift layout
- **WHEN** a pointer hovers over an enabled interactive control
- **THEN** the feedback is limited to subtle color, background, border, or text-decoration changes
- **AND** the control does not bounce, translate, scale, or otherwise visibly move

#### Scenario: Reduced motion disables nonessential transitions
- **WHEN** the user has `prefers-reduced-motion: reduce`
- **THEN** nonessential CSS transitions for interactive controls are disabled

### Requirement: Web frontend tablet and small-desktop responsive layouts
The web frontend SHALL provide intermediate responsive layout rules between the desktop layout and the existing `720px` mobile layout.

#### Scenario: Dashboard remains stable at tablet widths
- **WHEN** the Dashboard is viewed around `900px` or `1024px` viewport width
- **THEN** the dashboard grid, metric rows, and operations area fit without obvious crowding or horizontal page overflow
- **AND** the layout preserves the existing single-column behavior below `720px`

#### Scenario: Signal Detail remains stable at tablet widths
- **WHEN** the Signal Detail page is viewed around `900px` or `1024px` viewport width
- **THEN** the metadata block and target holdings table container fit within the page without causing horizontal page overflow
- **AND** any table overflow remains contained within the table scroll container

#### Scenario: Backtest Detail remains stable at tablet widths
- **WHEN** the Backtest Detail page is viewed around `900px` or `1024px` viewport width
- **THEN** metric cards, equity curve content, equity summary, and parameter summary fit without obvious crowding or horizontal page overflow
- **AND** the layout preserves the existing desktop behavior at `1200px` and above

### Requirement: Signal Detail holdings table numeric alignment
The web frontend SHALL render the Signal Detail target holdings table with report-like typography, numeric alignment, and restrained dividers while preserving the existing table structure and behavior.

#### Scenario: Numeric holdings columns align for scanning
- **WHEN** the Signal Detail page renders target holdings
- **THEN** target weight, rank, and score cells MUST use tabular numerals and right alignment
- **AND** their matching headers MUST align with those numeric cells
- **AND** exchange, symbol, and fallback text columns MUST remain left-aligned and readable

#### Scenario: Holdings table uses restrained header and hairline rhythm
- **WHEN** the Signal Detail target holdings table renders
- **THEN** the header MUST use the existing Slate and micro/caption typography hierarchy
- **AND** body rows MUST use Mist hairline separators with the final row divider removed
- **AND** row padding and line height MUST remain consistent with the editorial data style in `DESIGN.md`

#### Scenario: Holdings table preserves narrow-screen scrolling
- **WHEN** the Signal Detail page is viewed on a narrow viewport
- **THEN** the target holdings table MUST keep horizontal scrolling through `holdings-table-wrap`
- **AND** the implementation MUST preserve existing table DOM structure, rendered text, API calls, route behavior, and test selectors

### Requirement: Shared status states use restrained Ember accents
The web frontend SHALL keep empty, error, and operation status surfaces primarily achromatic, reserving Ember Orange for small functional accents rather than broad error presentation.

#### Scenario: Error surfaces avoid broad Ember rails
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders page-level error feedback
- **THEN** the error surface MUST use neutral project tokens for its primary border, text, and background treatment
- **AND** it MUST NOT rely on an Ember Orange rail or filled chromatic block as the main error identifier
- **AND** existing `role="alert"`, `aria-live`, and error message text MUST remain unchanged

#### Scenario: Operation failed states remain recognizable without Ember as the status color
- **WHEN** Dashboard operation feedback renders failed or partial-failure summaries
- **THEN** the summary surface MUST remain visually distinct using neutral borders, text hierarchy, and existing status copy
- **AND** Ember Orange MAY be used only for small functional punctuation such as operation link underlines
- **AND** existing operation result text, guidance, and route behavior MUST remain unchanged

#### Scenario: Empty and non-error states stay visually unified
- **WHEN** loading, empty, success, info, not-found, partial, or failed states render
- **THEN** they MUST continue to use the shared tokenized status presentation
- **AND** the implementation MUST NOT introduce red, blue, green, new status color systems, skeleton loaders, or feedback component rewrites

### Requirement: Dashboard focused first-screen hierarchy
The web frontend SHALL present the Dashboard first screen so local workflow status, key research metrics, and primary operations are discoverable before secondary historical details.

#### Scenario: Dashboard prioritizes key workflow areas
- **WHEN** the Dashboard route renders a successful dashboard aggregate response
- **THEN** the first screen presents the Dashboard load state, market data status, latest signal or signal empty state, and Operations entry point before dense secondary history dominates the page
- **AND** the Dashboard remains a local research workflow surface without marketing hero content, decorative artwork, login, account, hosting, deployment, or production language

#### Scenario: Operations remains discoverable with populated data
- **WHEN** the Dashboard route renders populated market data, strategy, latest signal, recent backtest, and recent fetch log data
- **THEN** the Operations section remains visible near the main workflow summary or reachable without passing through an unbounded history region
- **AND** the market data fetch, full fetch, generate signal, and run backtest controls keep their existing labels and behavior

#### Scenario: Empty workflow states point to matching actions
- **WHEN** the Dashboard route renders missing market data, missing latest signal, or missing recent backtest states
- **THEN** each empty state identifies the matching local Dashboard action or Operations control needed next
- **AND** the matching action remains available from the Dashboard without introducing new routes or remote setup assumptions

### Requirement: Dashboard long-content layout resilience
The web frontend SHALL prevent secondary Dashboard content from stretching unrelated cards or pushing primary workflow actions deep below the first screen.

#### Scenario: Recent fetch history does not stretch sibling cards
- **WHEN** the Dashboard receives multiple recent fetch log summaries or long fetch error text
- **THEN** the Recent fetches area is visually bounded or internally scrollable
- **AND** sibling Dashboard panels in the same layout region do not expand to match the full history height
- **AND** Operations remains positioned as a primary workflow area rather than after an unbounded history block

#### Scenario: Dashboard cards preserve readable density
- **WHEN** Dashboard panel content contains long paths, timestamps, failed symbols, or error summaries
- **THEN** the content wraps, clips, scrolls, or is otherwise contained within the relevant panel without causing horizontal page overflow
- **AND** the implementation does not hide the panel heading or primary value labels needed to understand the content

#### Scenario: Responsive layouts preserve the focused order
- **WHEN** the Dashboard is viewed at desktop, tablet, and mobile widths
- **THEN** status, key metrics, and Operations remain ordered ahead of secondary dense history
- **AND** the layout preserves the existing single-column mobile behavior below `720px`

### Requirement: Minimal visual emphasis system
The web frontend SHALL use a restrained emphasis system where only primary workflow actions and abnormal states receive strong visual weight.

#### Scenario: Primary and secondary dashboard content have distinct weight
- **WHEN** the Dashboard renders populated workflow data
- **THEN** market data status, latest signal state, and Operations controls have stronger visual priority than strategy details and recent fetch history
- **AND** the distinction is achieved with existing typography, spacing, surface, border, and accent tokens rather than new colors or broad chromatic blocks

#### Scenario: Detail pages keep consistent data-card treatment
- **WHEN** Signal Detail or Backtest Detail renders loading, empty, error, or populated states
- **THEN** page surfaces, cards, tables, and feedback states remain visually consistent with the Dashboard token system
- **AND** the pages do not introduce a competing visual palette, new dependency, or unrelated component pattern

#### Scenario: API metadata is visually secondary
- **WHEN** the App Shell renders the API base URL metadata
- **THEN** the metadata remains available but does not compete with the page title, key workflow status, or primary actions for visual attention


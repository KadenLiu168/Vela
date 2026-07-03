# http-api-service Specification

## Purpose
Define the local Vela HTTP API service skeleton, startup command, health endpoint, and boundary between API entrypoints and core business logic.
## Requirements
### Requirement: HTTP API service skeleton
The repository SHALL include an `apps/api` FastAPI service skeleton that can be imported and tested without starting a network server.

#### Scenario: API app is importable
- **WHEN** a developer imports the API application object
- **THEN** the import succeeds from the `vela_api` package

### Requirement: API startup command
The API service SHALL provide a documented root-level startup command named `uv run vela-api`.

#### Scenario: Developer starts the API service
- **WHEN** a developer runs `uv run vela-api`
- **THEN** the command starts the FastAPI service using uvicorn

### Requirement: API health endpoint
The API service SHALL expose `GET /api/health` as the minimal local health endpoint.

#### Scenario: Health endpoint returns healthy status
- **WHEN** a client sends `GET /api/health`
- **THEN** the response status is 200 and the response body reports healthy service status

### Requirement: API service boundary
The API service SHALL keep strategy and data-processing behavior in `vela_core` and SHALL NOT duplicate strategy logic in API entrypoints.

#### Scenario: API skeleton adds no strategy endpoint
- **WHEN** a developer inspects the initial API routes
- **THEN** only the health endpoint is exposed by this change

### Requirement: API database session factory
The API service SHALL configure a SQLAlchemy session factory using the shared default local SQLite database URL.

#### Scenario: API app has a default session factory
- **WHEN** the API application is created
- **THEN** the app has a session factory built from the shared default database URL

### Requirement: API request database session dependency
The API service SHALL provide a request-scoped database session dependency that reuses the core managed session lifecycle.

#### Scenario: Request work succeeds
- **WHEN** an API request uses the database session dependency and completes successfully
- **THEN** the session work is committed and the session is closed

#### Scenario: Request work fails
- **WHEN** an API request uses the database session dependency and raises an exception
- **THEN** the session work is rolled back, the session is closed, and the exception remains visible to the request handler

### Requirement: API database boundary
The API service SHALL expose database session wiring for routes without adding unrelated business behavior in the database wiring layer.

#### Scenario: API endpoint surface remains minimal
- **WHEN** a developer inspects the API routes after database wiring is added
- **THEN** no strategy, market data, signal, or backtest endpoint has been added by the database wiring change itself

### Requirement: API config read endpoint
The API service SHALL expose `GET /api/config` as a read-only endpoint that returns the current strategy configuration summary and ETF pool summary.

#### Scenario: Config endpoint returns current strategy summary
- **WHEN** a client sends `GET /api/config`
- **THEN** the response status is 200 and the response includes the `strategy_id`, version, universe config path, momentum windows, score weights, trend filter, selection, defense asset, costs, and performance settings loaded from `config/strategy_v1.yaml`

#### Scenario: Config endpoint returns ETF pool summary
- **WHEN** a client sends `GET /api/config`
- **THEN** the response includes the ETF pool id, version, description, provider, currency, total ETF count, active ETF count, and ETF identity rows loaded from the configured ETF pool file

### Requirement: API config endpoint uses real config loading
The API config endpoint SHALL use the existing application configuration loader and checked-in configuration files instead of mock data.

#### Scenario: Config endpoint validates real checked-in configuration
- **WHEN** the config endpoint builds its response
- **THEN** it loads the current strategy config and referenced ETF pool through the existing `vela_core` configuration loading capability

### Requirement: API read-only config boundary
The API config endpoint SHALL NOT edit configuration files, calculate strategy outputs, or access the database.

#### Scenario: Config endpoint is read-only
- **WHEN** a client sends `GET /api/config`
- **THEN** the endpoint returns configuration summary data without mutating config files or requiring a database session

### Requirement: API dashboard aggregate endpoint
The API service SHALL expose `GET /api/dashboard` as a read-only endpoint that returns the local Dashboard aggregate state.

#### Scenario: Dashboard endpoint returns aggregate state
- **WHEN** a client sends `GET /api/dashboard`
- **THEN** the response status is 200
- **AND** the response includes strategy summary, market data status, latest successful signal summary, and recent backtest summary fields

#### Scenario: Dashboard endpoint uses request database session
- **WHEN** the dashboard endpoint builds market, signal, and backtest summary data
- **THEN** it uses the API request-scoped database session dependency
- **AND** it delegates aggregation behavior to the core dashboard aggregation service

### Requirement: API dashboard integration validation
The dashboard endpoint SHALL be validated against a real local SQLite database and existing ORM models.

#### Scenario: Dashboard endpoint reads persisted SQLite rows
- **WHEN** a test API app is configured with a temporary SQLite database containing `MarketPrice`, `StrategySignal`, and `BacktestRun` rows
- **THEN** `GET /api/dashboard` returns aggregate values derived from those persisted rows
- **AND** the latest signal summary uses the latest successful persisted signal
- **AND** the latest signal summary includes fallback status derived from persisted `StrategySignalPosition` rows
- **AND** the validation does not rely only on mocked dashboard data

### Requirement: API dashboard empty workflow validation
The API service SHALL validate that `GET /api/dashboard` returns empty workflow values from a real empty local SQLite database.

#### Scenario: Dashboard endpoint returns empty workflow data
- **WHEN** an API integration test configures the app with a temporary SQLite database containing no market prices, successful signals, or backtests
- **THEN** `GET /api/dashboard` returns zero market price rows
- **AND** it returns zero covered ETFs
- **AND** it returns null latest signal data
- **AND** it returns null recent backtest data
- **AND** the validation does not rely on mocked dashboard data

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

### Requirement: API dashboard returns recent fetch logs
The API service SHALL return recent market data fetch log summaries from the dashboard aggregate response.

#### Scenario: Dashboard endpoint includes recent fetch logs
- **WHEN** an API integration test configures the app with a temporary SQLite database containing `DataFetchLog` rows
- **THEN** `GET /api/dashboard` returns recent fetch log summaries derived from those persisted rows
- **AND** the validation does not rely only on mocked dashboard data

### Requirement: API strategy signal generation endpoint
The API service SHALL expose a strategy signal generation command endpoint at `POST /api/strategy-signals/generate`.

#### Scenario: Generate strategy signal for explicit date
- **WHEN** a client sends `POST /api/strategy-signals/generate?signalDate=2026-06-23`
- **THEN** the API calls the existing core `generate_strategy_signal` capability for `2026-06-23`
- **AND** the response status is 200
- **AND** the response includes signal id, signal date, config version, status, result, error message, and positions

#### Scenario: Generate strategy signal for latest local market date
- **WHEN** a client sends `POST /api/strategy-signals/generate` without `signalDate`
- **THEN** the API uses the latest local `MarketPrice.trade_date` as the signal date
- **AND** the API calls the existing core `generate_strategy_signal` capability for that date
- **AND** the response includes the generated signal fields and positions

#### Scenario: Reject missing local market date
- **WHEN** a client sends `POST /api/strategy-signals/generate` without `signalDate` and the local database has no market prices
- **THEN** the API rejects the request before running signal generation

#### Scenario: No JSON body schema
- **WHEN** a client calls the strategy signal generation endpoint
- **THEN** the endpoint accepts `signalDate` only as an optional query parameter

### Requirement: API strategy signal generation integration validation
The API strategy signal generation endpoint SHALL be validated with the local API app, a temporary SQLite database, and the existing backend signal generation workflow.

#### Scenario: Generate endpoint persists signal rows to SQLite
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/strategy-signals/generate`
- **THEN** the response contains values produced by the existing core generation workflow
- **AND** the generated `StrategySignal` and `StrategySignalPosition` rows are persisted in SQLite
- **AND** the validation does not rely only on mocked signal generation results

### Requirement: API latest strategy signal structured endpoint
The API service SHALL expose `GET /api/strategy-signals/latest` as a read-only endpoint that returns the latest successful persisted strategy signal as structured JSON.

#### Scenario: Latest signal endpoint returns structured signal data
- **WHEN** a client sends `GET /api/strategy-signals/latest` and a successful persisted strategy signal exists
- **THEN** the response status is 200
- **AND** the response includes `has_signal: true`
- **AND** the response includes signal metadata with signal id, signal date, config version, generated timestamp, result, and fallback status
- **AND** the response includes target positions with ETF identity, target weight, rank, score, and per-position fallback status

#### Scenario: Latest signal endpoint returns stable empty state
- **WHEN** a client sends `GET /api/strategy-signals/latest` and no successful persisted strategy signal exists
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: false`
- **AND** the response body includes `signal: null`
- **AND** the response body includes an empty `positions` list

#### Scenario: Latest signal endpoint has no date filter
- **WHEN** a client calls the latest signal endpoint
- **THEN** the endpoint does not require or define a `signalDate` filter

### Requirement: API latest strategy signal integration validation
The API latest strategy signal endpoint SHALL be validated with the local API app, a temporary SQLite database, and real `StrategySignal` and `StrategySignalPosition` rows.

#### Scenario: Latest signal endpoint reads persisted SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing multiple persisted strategy signals and positions
- **THEN** `GET /api/strategy-signals/latest` returns the newest successful signal by generated timestamp and id tie-breaker
- **AND** it ignores failed, running, and partial signals
- **AND** it derives fallback status from persisted position rank and score values
- **AND** the validation does not rely only on mocked signal report data

### Requirement: API run backtest endpoint
The API service SHALL expose a run backtest command endpoint at `POST /api/backtests/run`.

#### Scenario: Run backtest for explicit date range
- **WHEN** a client sends `POST /api/backtests/run?startDate=2026-01-01&endDate=2026-01-31`
- **THEN** the API calls the existing core `run_backtest` capability for that date range
- **AND** the response status is 200
- **AND** the response includes run id, status, start date, end date, trading day count, signal count, total return, annualized return, max drawdown, volatility, and Sharpe ratio

#### Scenario: Reject invalid backtest date range
- **WHEN** a client sends `POST /api/backtests/run` with `startDate` after `endDate`
- **THEN** the API rejects the request without persisting a backtest run

#### Scenario: No JSON body schema
- **WHEN** a client calls the run backtest endpoint
- **THEN** the endpoint accepts `startDate` and `endDate` only as required query parameters

### Requirement: API run backtest integration validation
The API run backtest endpoint SHALL be validated with the local API app, a temporary SQLite database, and the existing backend backtest workflow.

#### Scenario: Run backtest endpoint persists SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/backtests/run` with a valid date range
- **THEN** the response contains values produced by the existing core backtest workflow
- **AND** the generated `BacktestRun` and `BacktestEquityCurve` rows are persisted in SQLite
- **AND** the validation does not rely only on mocked backtest results

### Requirement: API recent backtest list endpoint
The API service SHALL expose `GET /api/backtests` as a read-only endpoint that returns recent persisted backtest runs.

#### Scenario: Recent backtest list returns persisted runs
- **WHEN** a client sends `GET /api/backtests`
- **THEN** the response status is 200
- **AND** the response includes a `runs` list derived from persisted `BacktestRun` rows
- **AND** each run includes run id, start date, end date, status, started timestamp, finished timestamp, total return, annualized return, maximum drawdown, volatility, and Sharpe ratio
- **AND** the runs are ordered by newest start timestamp with run id as the tie-breaker

#### Scenario: Recent backtest list supports limit
- **WHEN** a client sends `GET /api/backtests?limit=1`
- **THEN** the response status is 200
- **AND** the response includes no more than one run

#### Scenario: Recent backtest list returns empty list
- **WHEN** a client sends `GET /api/backtests` and no backtest runs exist
- **THEN** the response status is 200
- **AND** the response includes an empty `runs` list

### Requirement: API recent backtest list integration validation
The API recent backtest list endpoint SHALL be validated with the local API app, a temporary SQLite database, and real `BacktestRun` rows.

#### Scenario: List endpoint reads persisted SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing multiple `BacktestRun` rows
- **THEN** `GET /api/backtests` returns values derived from those persisted rows
- **AND** the validation does not rely only on mocked backtest list data

### Requirement: API backtest detail endpoint
The API service SHALL expose `GET /api/backtests/{run_id}` as a read-only endpoint that returns one persisted backtest run with its equity curve.

#### Scenario: Backtest detail returns persisted run data
- **WHEN** a client sends `GET /api/backtests/{run_id}` for an existing run
- **THEN** the response status is 200
- **AND** the response includes run metadata with run id, strategy name, config version, start date, end date, parameters JSON, status, error message, started timestamp, and finished timestamp
- **AND** the response includes metrics with total return, annualized return, maximum drawdown, volatility, and Sharpe ratio
- **AND** the response includes an `equity_curve` list derived from persisted `BacktestEquityCurve` rows

#### Scenario: Backtest detail orders equity curve by trade date
- **WHEN** a persisted run has multiple equity curve rows
- **THEN** `GET /api/backtests/{run_id}` returns the equity curve points ordered by trade date ascending

#### Scenario: Backtest detail returns stable not found error
- **WHEN** a client sends `GET /api/backtests/{run_id}` for a missing run id
- **THEN** the response status is 404
- **AND** the response body is a stable not-found error

### Requirement: API backtest detail integration validation
The API backtest detail endpoint SHALL be validated with the local API app, a temporary SQLite database, and real persisted `BacktestRun` and `BacktestEquityCurve` rows.

#### Scenario: Detail endpoint reads persisted SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing a `BacktestRun` and related `BacktestEquityCurve` rows
- **THEN** `GET /api/backtests/{run_id}` returns values derived from those persisted rows
- **AND** the validation does not rely only on mocked backtest detail data

### Requirement: API stable error response envelope
The API service SHALL return non-2xx failures as a stable JSON object containing `error.code`, `error.category`, and `error.message`.

#### Scenario: Validation failure uses stable envelope
- **WHEN** a client sends an invalid request that fails FastAPI request validation
- **THEN** the response status is 422
- **AND** the response body contains `error.category` equal to `validation`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

#### Scenario: Not found failure uses stable envelope
- **WHEN** a client requests a missing persisted resource
- **THEN** the response status is 404
- **AND** the response body contains `error.category` equal to `not_found`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

#### Scenario: Operation failure uses stable envelope
- **WHEN** an API route detects an expected operation failure such as missing local market prices, invalid backtest dates, configuration loading failure, or provider workflow failure
- **THEN** the response body contains `error.category` equal to `operation_failed`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

#### Scenario: Unexpected failure uses stable envelope
- **WHEN** an API route raises an otherwise unhandled exception
- **THEN** the response status is 500
- **AND** the response body contains `error.category` equal to `unexpected`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

### Requirement: API error path integration validation
The API service SHALL validate stable error responses through real FastAPI routes and backend exception paths.

#### Scenario: Real route validation covers API errors
- **WHEN** the API error response tests run
- **THEN** they exercise real API route calls with `TestClient`
- **AND** they cover validation, not-found, no-market-data, date-range, configuration, provider workflow, and unexpected error paths
- **AND** they do not rely only on frontend request mocks

### Requirement: API first-version interface contract validation
The API service SHALL validate the first-version API interface surface through real FastAPI route calls.

#### Scenario: Interface tests cover first-version endpoint success responses
- **WHEN** the API interface contract tests run
- **THEN** they MUST call `GET /api/health`, `GET /api/config`, `GET /api/dashboard`, `POST /api/market-data/fetch`, `POST /api/strategy-signals/generate`, `GET /api/strategy-signals/latest`, `GET /api/backtests`, `POST /api/backtests/run`, and `GET /api/backtests/{run_id}` through `TestClient`
- **AND** they MUST assert stable top-level response structures for each successful endpoint family

#### Scenario: Interface tests cover empty persistence states
- **WHEN** the API interface contract tests run against an empty temporary SQLite database
- **THEN** they MUST validate stable empty response structures for dashboard, latest signal, and backtest list endpoints
- **AND** they MUST not rely only on mocked backend return values

#### Scenario: Interface tests cover key API error paths
- **WHEN** the API interface contract tests run
- **THEN** they MUST validate request validation, missing resource, missing market data, invalid date range, configuration failure, and provider workflow failure paths
- **AND** non-2xx failures MUST use the stable `error.code`, `error.category`, and `error.message` response envelope

#### Scenario: Interface tests exercise real backend paths
- **WHEN** API interface tests cover dashboard, latest signal, backtest list, backtest detail, signal generation, or backtest execution
- **THEN** they MUST use temporary SQLite data and existing backend workflows or persisted ORM rows
- **AND** market data fetch tests MAY use a controlled provider but MUST verify the resulting response and persistence behavior through the API route

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

### Requirement: API backtest run to detail closed-loop validation
The API service SHALL validate that a successful run-backtest request persists a backtest result that is visible through the backtest detail API from the same local SQLite database.

#### Scenario: Run endpoint updates backtest detail read state
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/backtests/run` with a valid date range
- **AND** the client then sends `GET /api/backtests/{run_id}` for the returned run id against the same API app and database
- **THEN** the run response reports values produced by the existing backtest workflow
- **AND** the generated `BacktestRun` and ordered `BacktestEquityCurve` rows are persisted in SQLite
- **AND** the detail response identifies the same run id
- **AND** the detail response includes metric cards source data and equity curve rows for the generated run


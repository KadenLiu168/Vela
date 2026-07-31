# http-api-service Specification

## Purpose
Defines the FastAPI service surface, including the local-development `POST /api/setup/bootstrap` endpoint.
## Requirements
### Requirement: API setup bootstrap endpoint
The API service SHALL expose `POST /api/setup/bootstrap` as a local-development endpoint that runs the compound local setup bootstrap operation.

#### Scenario: Endpoint returns success aggregate
- **WHEN** a client posts to `/api/setup/bootstrap` against an empty local database
- **THEN** the response status is 200
- **AND** the response body includes a top-level `status` field, a `steps` array with one entry per bootstrap step, a `failed_step` field, and a `total_duration_seconds` field

#### Scenario: Endpoint reports step failure without 5xx
- **WHEN** a client posts to `/api/setup/bootstrap` and a non-first step fails for a known business reason
- **THEN** the response status is 200
- **AND** the response body's top-level `status` is `"failed"`
- **AND** the response body's `failed_step` identifies the failing step
- **AND** the failing step's entry in `steps` includes an `error_message`

#### Scenario: Endpoint scoped to local development
- **WHEN** a developer reads the documentation for `POST /api/setup/bootstrap`
- **THEN** the documentation states that the endpoint is intended for local development setup only
- **AND** the documentation states that production database migrations must continue to use the `vela init-db` CLI command

### Requirement: API strategy signal list endpoint
The API service SHALL expose `GET /api/strategy-signals` returning a paginated list of successful strategy signal summaries scoped to the current `strategy_id` and `config_version`. The endpoint SHALL accept an optional `source` query parameter filtering by `manual`, `scheduled`, `backtest`, or `legacy`. Omitting `source` SHALL return signals of all sources. Any supplied value outside the four-value enum, including an empty value or the string `null`, SHALL be rejected at the query-parameter layer with 422.

#### Scenario: Endpoint returns filtered summaries
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** the response status is 200
- **AND** the response body includes a `signals` array of summaries whose `strategy_id` and `config_version` match the current strategy config
- **AND** only `success`-status signals are included
- **AND** summaries are ordered by `generated_at` descending then `id` descending

#### Scenario: Endpoint honors limit and offset
- **WHEN** a client requests `GET /api/strategy-signals?limit=20&offset=40`
- **THEN** the response contains at most 20 summaries starting at offset 40

#### Scenario: Source filter narrows results
- **WHEN** a client requests `GET /api/strategy-signals?source=backtest`
- **THEN** every entry in the `signals` array has `source` equal to `backtest`
- **AND** entries whose `source` is not `backtest` are excluded before limit and offset are applied

#### Scenario: Every declared source is accepted
- **WHEN** a client requests the endpoint once for each value in `StrategySignal.SOURCES`
- **THEN** each request passes query validation
- **AND** any returned entry has the requested source

#### Scenario: Invalid source is rejected
- **WHEN** a client supplies an unknown, empty, or literal `null` source value
- **THEN** the response status is 422
- **AND** the response body uses the stable API error shape with category `validation`

#### Scenario: Empty history returns empty array
- **WHEN** a client requests `GET /api/strategy-signals` and no successful signal exists for the current strategy and version
- **THEN** the response body's `signals` array is empty

### Requirement: API strategy signal detail endpoint
The API service SHALL expose `GET /api/strategy-signals/{signal_id}` returning the metadata and target positions of one strategy signal by id, scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns signal detail
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an existing id that belongs to the current strategy and version
- **THEN** the response status is 200
- **AND** the response body includes the signal metadata and a `positions` array
- **AND** each position in the `positions` array includes the ETF's human-readable `name` (joined from `etf_info.name`), in addition to `exchange`, `symbol`, `target_weight`, `rank`, `score`, and `is_fallback`

#### Scenario: Unknown signal id returns 404
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy signal id returns 404
- **WHEN** a client requests a signal id whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

### Requirement: API backtest list endpoint
The API service SHALL expose `GET /api/backtests` returning a paginated list of backtest run summaries, filtered by `strategy_id` and `config_version` (defaulting to the current strategy config), ordered newest-started first.

#### Scenario: Endpoint returns summaries
- **WHEN** a client requests `GET /api/backtests`
- **THEN** the response status is 200
- **AND** the response body includes a `runs` array ordered by `started_at` descending then `id` descending
- **AND** each run summary includes `strategy_id` and `config_version`

#### Scenario: Endpoint defaults to current strategy filter
- **WHEN** a client requests `GET /api/backtests` without explicit filter params
- **THEN** only runs whose `strategy_id` and `config_version` match the current strategy config are included

#### Scenario: Endpoint honors limit and offset
- **WHEN** a client requests `GET /api/backtests?limit=10&offset=10`
- **THEN** the response contains at most 10 runs starting at offset 10

#### Scenario: Endpoint honors explicit strategy filter
- **WHEN** a client requests `GET /api/backtests?strategy_id=Dual_momentum&config_version=v1`
- **THEN** only runs matching both values are included

### Requirement: API backtest detail endpoint
The API service SHALL expose `GET /api/backtests/{run_id}` returning the detail of one backtest run by id, scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns run detail
- **WHEN** a client requests `GET /api/backtests/{run_id}` for an existing id that belongs to the current strategy and version
- **THEN** the response status is 200
- **AND** the response body includes run metadata (with `strategy_id`), metrics, and equity curve

#### Scenario: Unknown run id returns 404
- **WHEN** a client requests `GET /api/backtests/{run_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy run id returns 404
- **WHEN** a client requests a run id whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

### Requirement: API delegates strategy signal generation orchestration to core

The API service SHALL expose the strategy signal generation endpoint while delegating business workflow orchestration to the core strategy signal service. The endpoint SHALL remain responsible for HTTP query parameter handling, HTTP error mapping, and response formatting.

#### Scenario: Generate endpoint preserves successful response contract
- **WHEN** a client posts to `/api/strategy-signals/generate` and local market data is available
- **THEN** the endpoint returns status 200
- **AND** the response body includes the existing strategy signal response fields: `signal_id`, `signal_date`, `config_version`, `status`, `result`, `error_message`, and `positions`
- **AND** the signal generation and persistence workflow is performed by the core service

#### Scenario: Generate endpoint preserves explicit signal date behavior
- **WHEN** a client posts to `/api/strategy-signals/generate?signalDate=<date>`
- **THEN** the endpoint passes the parsed signal date to the core service
- **AND** the response reports that same signal date when generation succeeds

#### Scenario: Generate endpoint preserves missing market data error
- **WHEN** a client posts to `/api/strategy-signals/generate` and no local market prices exist
- **THEN** the endpoint returns status 400
- **AND** the response uses the stable API error shape with category `operation_failed`
- **AND** the error message states that no local market prices were found

#### Scenario: Transport layer does not duplicate core signal workflow
- **WHEN** maintainers inspect the API strategy signal generation endpoint
- **THEN** the endpoint does not directly load active ETFs, load price panels, build defensive ETF lookup maps, construct signal persistence callbacks, or convert generated positions into persistence inputs

### Requirement: API strategy signal latest endpoint
The API service SHALL expose `GET /api/strategy-signals/latest` returning the latest successful
strategy signal summary, metadata, and target positions scoped to the exact, case-sensitive current
`strategy_id` and `config_version`.

#### Scenario: Endpoint returns latest signal with positions
- **WHEN** a client requests `GET /api/strategy-signals/latest` and a successful signal exists for the current strategy id and config version
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: true`, a `signal` object, and a `positions` array
- **AND** signals belonging to other strategies or config versions are ignored
- **AND** each position in the `positions` array includes the ETF's human-readable `name` (joined from `etf_info.name`), in addition to `exchange`, `symbol`, `target_weight`, `rank`, `score`, and `is_fallback`

#### Scenario: No successful signal returns empty state
- **WHEN** a client requests `GET /api/strategy-signals/latest` and no successful signal exists for the current strategy id and config version
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: false`, a null `signal`, and an empty `positions` array

### Requirement: API strategy signal list endpoint exposes provenance

`GET /api/strategy-signals` SHALL include `source` and `backtest_run_id` on each summary, in addition to the existing fields.

#### Scenario: List item includes provenance
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** each entry in the `signals` array includes `source` (`manual`, `scheduled`, `backtest`, or `legacy`)
- **AND** each entry includes `backtest_run_id` (null for non-backtest and legacy signals)

#### Scenario: Existing list contract preserved
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** the existing fields (`signal_id`, `signal_date`, `config_version`, `result`, `generated_at`, `is_fallback`, `position_count`) remain present
- **AND** ordering, scoping, limit, and offset behavior are unchanged

### Requirement: API strategy signal detail endpoint exposes provenance

`GET /api/strategy-signals/{signal_id}` SHALL include `source` and `backtest_run_id` in the signal metadata.

#### Scenario: Detail includes provenance
- **WHEN** a client requests an existing signal detail
- **THEN** the `signal` object includes `source` and `backtest_run_id`

### Requirement: API generate endpoint accepts caller source

`POST /api/strategy-signals/generate` SHALL accept an optional `source` query parameter (allowed `manual`, `scheduled`; default `manual`) and SHALL return the recorded `source` in the response. It SHALL reject `source="backtest"` or any other value with HTTP 400.

#### Scenario: Default generate source is manual
- **WHEN** a client posts without `source`
- **THEN** the response `source` is `manual`
- **AND** the existing response fields are unchanged

#### Scenario: Scheduled generate source is recorded
- **WHEN** a client posts with `source=scheduled`
- **THEN** the response `source` is `scheduled`
- **AND** the persisted signal row's `source` is `scheduled`

#### Scenario: Unsupported source rejected on generate
- **WHEN** a client posts with `source=backtest`, `source=legacy`, or another unsupported value
- **THEN** the endpoint returns HTTP 400 with the stable API error shape
- **AND** no signal row is persisted

### Requirement: API backtest detail endpoint lists its signals

`GET /api/backtests/{run_id}` SHALL include the ids of the strategy signals produced by that run.

#### Scenario: Backtest detail includes signal ids
- **WHEN** a client requests an existing backtest run detail
- **THEN** the top-level response includes `signal_ids`, an array of `strategy_signal.id` values ordered by `signal_date` then `id`
- **AND** the response includes `signal_count` equal to the length of `signal_ids`
- **AND** existing run/metrics/equity-curve fields are unchanged

#### Scenario: Backtest with no linked signals has an explicit empty collection
- **WHEN** a client requests an existing legacy or manually created backtest run with no linked signals
- **THEN** top-level `signal_ids` is an empty array
- **AND** top-level `signal_count` is `0`

### Requirement: API backtest signals pagination endpoint
The API service SHALL expose `GET /api/backtests/{run_id}/signals` returning `{ "signals": [...] }` for signals linked to the given backtest run and scoped to the current `strategy_id` and `config_version`. Each summary SHALL include `signal_id`, `signal_date`, `result`, and `backtest_run_id`. The endpoint SHALL return every signal linked to the run without a status filter, so for a stable run the collection across pages matches the `signal_count` returned by `GET /api/backtests/{run_id}`. Results SHALL be ordered by `signal_date` ascending then `id` ascending. The endpoint SHALL accept `limit` from 1 through 100 (default 20) and `offset >= 0`. Unknown runs and runs outside the current strategy or config version SHALL return the same stable 404 shape.

#### Scenario: Endpoint returns paginated signal summaries
- **WHEN** a client requests `GET /api/backtests/{run_id}/signals?limit=20&offset=0` for an in-scope run with linked signals
- **THEN** the response status is 200
- **AND** the response body contains a `signals` array of at most 20 summaries
- **AND** each summary contains `signal_id`, `signal_date`, `result`, and `backtest_run_id`
- **AND** summaries are ordered by `signal_date` ascending then `signal_id` ascending

#### Scenario: Endpoint honors offset
- **WHEN** a client requests `GET /api/backtests/{run_id}/signals?limit=20&offset=40`
- **THEN** the response contains summaries starting at offset 40 in the stable ordering

#### Scenario: Unknown run id returns 404
- **WHEN** a client requests the endpoint for an id that no backtest run has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign strategy or config run returns 404
- **WHEN** a client requests the endpoint for a run whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body is indistinguishable from the unknown-run 404 response

#### Scenario: Invalid pagination is rejected
- **WHEN** a client supplies `limit=0`, `limit=101`, or a negative `offset`
- **THEN** the response status is 422
- **AND** the response body uses the stable API error shape with category `validation`

#### Scenario: Run with no linked signals returns empty collection
- **WHEN** a client requests the endpoint for an existing in-scope run with no linked signals
- **THEN** the response status is 200
- **AND** the response body equals `{ "signals": [] }`

#### Scenario: Signal collection matches signal_count
- **WHEN** a client requests successive pages for a stable in-scope run until exhausted
- **THEN** the concatenated signal ids contain no omissions or duplicates
- **AND** their total count equals the `signal_count` field of `GET /api/backtests/{run_id}`

### Requirement: Domain router composition preserves the HTTP surface
The API service SHALL compose its existing routes from domain-specific `APIRouter` modules while
retaining one application entry point importable as `vela_api.main:app`. Router composition SHALL
preserve every existing HTTP method, path, query parameter name/alias, validation bound, route
ordering requirement, and status-code behavior. Moving routes SHALL NOT duplicate core business
workflows or introduce a second API surface.

#### Scenario: Route inventory is unchanged
- **WHEN** tests compare the application route inventory before and after router composition
- **THEN** the same application-owned `(HTTP method, path)` pairs are present
- **AND** no existing endpoint is duplicated, removed, renamed, or version-prefixed

#### Scenario: Static and parameterized routes retain resolution
- **WHEN** a client requests existing static paths such as strategy-signal latest or backtest run
  alongside parameterized detail paths
- **THEN** each request resolves to the same endpoint behavior as before router composition
- **AND** path parameter validation does not capture a static route accidentally

#### Scenario: Application entry point remains compatible
- **WHEN** uvicorn, the CLI, or tests import `vela_api.main:app`
- **THEN** the composed FastAPI application is available at that path
- **AND** database initialization and existing exception-handler registration remain active

### Requirement: Successful API responses have concrete typed contracts
Every application-owned endpoint SHALL declare a concrete Pydantic success response model. The
models SHALL describe nested objects, arrays, optional fields, dates, datetimes, and scalar types in
OpenAPI and SHALL validate API-produced success payloads. Response modeling SHALL preserve the
existing JSON field names, nesting, nullability, ordering, and values, including Decimal-backed
financial values encoded as JSON strings.

#### Scenario: OpenAPI exposes concrete success schemas
- **WHEN** a client inspects the generated OpenAPI document
- **THEN** every application-owned endpoint's successful response references or contains a concrete
  schema instead of an unconstrained `additionalProperties: true` object
- **AND** nested signal, position, run, metric, curve, dashboard, config, fetch, and bootstrap
  fields have explicit types

#### Scenario: Decimal-backed values remain strings
- **WHEN** an endpoint returns target weights, scores, prices, returns, drawdown, volatility, or
  Sharpe values backed by `Decimal`
- **THEN** the JSON values remain strings or null exactly where the existing contract does
- **AND** their OpenAPI schema advertises the frontend-visible string/null representation

#### Scenario: Dates, datetimes, nulls, and empty collections remain compatible
- **WHEN** endpoint fixtures contain date/datetime fields, nullable fields, or empty arrays
- **THEN** the serialized response equals the existing wire value and shape
- **AND** response validation does not replace an empty array with null or omit an existing key

#### Scenario: Response drift fails validation
- **WHEN** API construction omits a required success field or supplies an incompatible field type
- **THEN** response-model validation rejects the server-produced payload
- **AND** the OpenAPI contract and runtime response cannot silently diverge

### Requirement: Routine API requests share lifespan application configuration
The API application SHALL load and validate one immutable `AppConfig` during lifespan startup and
provide it to routine config, dashboard, strategy-signal, and backtest endpoints through an
overridable dependency. A routine request SHALL NOT re-read strategy or ETF-pool YAML. Invalid
startup configuration SHALL prevent the application lifespan from becoming ready. The local setup
bootstrap endpoint SHALL retain its existing request-scoped `AppConfig` reload contract.

#### Scenario: Routine requests reuse one validated config
- **WHEN** multiple routine endpoints execute within one application lifespan
- **THEN** application config is loaded once during lifespan startup
- **AND** every routine endpoint receives the same immutable `AppConfig`
- **AND** no routine request calls the YAML loaders again

#### Scenario: Startup rejects invalid application config
- **WHEN** the configured strategy or referenced ETF-pool YAML cannot be read, parsed, or validated
  at application lifespan startup
- **THEN** startup fails with the project-owned configuration error
- **AND** the application does not begin serving routine requests with missing or partial config

#### Scenario: Tests override application config deterministically
- **WHEN** an API test supplies a validated test-owned `AppConfig` through the config dependency
- **THEN** endpoints use that exact object without reading checked-in mutable config
- **AND** the override is scoped to the test application and does not leak to another app instance

#### Scenario: Bootstrap keeps current request-scoped config
- **WHEN** two bootstrap requests run in one process and the resolved config changes between them
- **THEN** bootstrap loads `AppConfig` once for each request as required by
  `local-setup-bootstrap`
- **AND** routine endpoints continue using the lifespan config until the application is restarted

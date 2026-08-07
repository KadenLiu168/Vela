# http-api-service Specification

## Purpose
Defines the FastAPI service surface, including the local-development `POST /api/setup/bootstrap` endpoint.
## Requirements
### Requirement: API lists current-strategy Walk-forward evaluations
The API SHALL expose `GET /api/walk-forwards` scoped to the configured `strategy_id`, with `limit` 1..100 (default 10), non-negative `offset` (default 0), exact total, and stable `finished_at DESC, run_id DESC` ordering. It SHALL expose no `strategyId` filter and MUST NOT start or mutate a Walk-forward execution.

#### Scenario: History returns a stable page and total
- **WHEN** a client requests `GET /api/walk-forwards?limit=10&offset=10`
- **THEN** the response contains at most ten current-strategy summaries and the exact current-strategy total

### Requirement: API returns one typed Walk-forward evaluation detail
The API SHALL expose `GET /api/walk-forwards/{run_id}` with typed ISO dates/timestamps, persisted decimal strings, provenance/evidence versions and checksums, manifest, aggregate evidence, ordered windows, OOS links, fixed benchmark data, and a non-null `stitched_oos` result derived from authoritative persisted evidence. `stitched_oos.status` SHALL be `available` when the windows are contiguous or `unavailable_non_contiguous_windows` when otherwise valid windows have a gap or overlap. An available result SHALL contain Decimal strings `initial_net_value`, `ending_net_value`, and `total_return`, plus chronological `points`; every point SHALL contain ISO `trade_date`, six-place Decimal-string `net_value`, integer `window_ordinal`, and boolean `is_window_start`. An unavailable result SHALL contain null cumulative values and an empty points list while the rest of the detail remains complete. Unknown and other-strategy ids SHALL use the standard 404 contract. Unsupported or corrupt persisted documents, OOS ownership, eligible source curves, or official-session manifests SHALL use the standard unexpected-error contract without partial detail data.

#### Scenario: Detail preserves ordered ownership
- **WHEN** a current-strategy persisted evaluation with valid adjacent OOS windows is requested
- **THEN** each window exposes its selected OOS run and both fixed benchmarks in chronological order
- **AND** `stitched_oos.status` is `available` and exposes the deterministic compounded points and cumulative result in the same window order

#### Scenario: Reset boundary is machine-readable
- **WHEN** a Walk-forward detail contains more than one stitched OOS segment
- **THEN** the first point for each segment identifies its owning `window_ordinal` and has `is_window_start = true`
- **AND** every later point in that segment has `is_window_start = false`

#### Scenario: Invalid stitched evidence returns no partial detail
- **WHEN** contiguous persisted windows are eligible for stitching but their OOS curves or official-session manifest is corrupt
- **THEN** the API returns the standard unexpected-error envelope
- **AND** it does not return windows, a partial curve, or a cumulative result

#### Scenario: Non-contiguous windows preserve complete detail
- **WHEN** a valid persisted evaluation has an official-session gap or overlap between ordered OOS windows
- **THEN** the API returns the complete Walk-forward detail with `stitched_oos.status = unavailable_non_contiguous_windows`
- **AND** cumulative values are null and points are empty

### Requirement: Walk-forward API is read-only
The HTTP service SHALL expose `GET /api/walk-forwards`, `GET /api/walk-forwards/{run_id}`, and `POST /api/walk-forwards/run` for this history. The `POST /api/walk-forwards/run` endpoint SHALL be the only mutation route and SHALL only start a new asynchronous Walk-forward execution; the service MUST NOT add any endpoint that retries, edits, or deletes a Walk-forward execution, and MUST NOT expose any endpoint that mutates an existing `WalkForwardRun` row other than the status transition performed by the runner itself (`running` → `success` | `failed`).

#### Scenario: OpenAPI exposes only history reads
- **WHEN** a client inspects the Walk-forward read surface in OpenAPI
- **THEN** exactly the two GET history/detail paths are present and remain read-only
- **AND** no retry, edit, or delete path is present

#### Scenario: OpenAPI exposes history reads plus run trigger
- **WHEN** a client inspects Walk-forward paths in OpenAPI
- **THEN** exactly three Walk-forward paths are present: the two GET history/detail paths and one POST run-trigger path
- **AND** no retry, edit, or delete path is present

### Requirement: Expected API failures use typed domain mapping

The API service SHALL map expected domain failures by exception type through a
central transport-layer mapping. It MUST NOT choose an HTTP status, error code,
or error category by matching exception-message text, and it MUST NOT classify
an arbitrary `ValueError` as a client error. Existing specified failures MUST
retain their stable HTTP status and error-envelope semantics.

#### Scenario: Missing market data retains its contract
- **WHEN** strategy signal generation raises the typed missing-market-data error
- **THEN** the API returns status 400
- **AND** the response uses code `no_market_data` and category `operation_failed`
- **AND** the message states that no local market prices were found

#### Scenario: Invalid date range retains its contract
- **WHEN** an operation raises the typed invalid-date-range error
- **THEN** the API returns status 400
- **AND** the response uses code `invalid_date_range` and category `operation_failed`

#### Scenario: Error wording does not control classification
- **WHEN** an unclassified exception has the same message as a known domain error
- **THEN** the API does not map it as that known domain error
- **AND** the unexpected-error contract applies

#### Scenario: Arbitrary ValueError remains unexpected
- **WHEN** an endpoint or core operation raises a `ValueError` that is not a typed expected domain failure
- **THEN** the API returns status 500
- **AND** the response uses the generic unexpected-error envelope without exposing the exception detail

### Requirement: API requests are correlated by request ID

The API service SHALL assign one effective request ID to every request, expose
it in the `X-Request-ID` response header, and include it in the corresponding
request completion and unexpected-error logs. The service SHALL reuse a
caller-provided ID only when it satisfies the documented bounded safe-token
format; otherwise it SHALL generate a new UUID.

#### Scenario: Server generates a request ID
- **WHEN** a client sends a successful request without `X-Request-ID`
- **THEN** the response includes a non-empty `X-Request-ID` header
- **AND** the request completion log contains the same value

#### Scenario: Safe caller request ID is preserved
- **WHEN** a client supplies an allowed `X-Request-ID` value
- **THEN** the response header contains that same value
- **AND** request and exception logs for the request use that value

#### Scenario: Unsafe caller request ID is replaced
- **WHEN** a caller supplies an empty, over-length, or disallowed-character request ID
- **THEN** the service generates a different valid request ID
- **AND** the untrusted value is not emitted in logs

#### Scenario: Error responses remain correlated
- **WHEN** validation, typed-domain, explicit HTTP, or unexpected error handling produces a response
- **THEN** the response includes the effective `X-Request-ID`
- **AND** the existing JSON error-envelope fields and meanings remain unchanged

### Requirement: API request completion logs are bounded and safe

The API service SHALL emit one completion log per request containing the
effective request ID, HTTP method, normalized route template when available,
response status, and monotonic duration. Request completion logs MUST NOT
include request bodies, raw query strings, credentials, or exception details.

#### Scenario: Successful request emits completion context
- **WHEN** an API request completes successfully
- **THEN** exactly one request completion event records request ID, method, normalized route, status, and duration

#### Scenario: Failed request emits completion context
- **WHEN** an API request produces a handled or unexpected error response
- **THEN** exactly one request completion event records request ID, method, normalized route, status, and duration
- **AND** the event excludes the request body and raw query string

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
The API service SHALL expose `GET /api/strategy-signals/{signal_id}` returning the metadata and target positions of one strategy signal by id, scoped to the current `strategy_id` regardless of `config_version`. Signal list/latest endpoints SHALL retain their current version-filtered behavior.

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
The API service SHALL expose `GET /api/backtests/{run_id}` returning the detail of one backtest run by id, scoped to the current `strategy_id` regardless of `config_version`. Backtest list defaults and explicit version filters SHALL remain unchanged.

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
The API service SHALL expose `GET /api/backtests/{run_id}/signals` returning `{ "signals": [...] }` for signals linked to the given backtest run and scoped to the current `strategy_id` regardless of `config_version`. Each summary SHALL include `signal_id`, `signal_date`, `result`, and `backtest_run_id`; ordering and pagination semantics remain unchanged. Unknown runs and runs outside the current strategy SHALL return the same stable 404 shape.

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

### Requirement: API backtest responses expose benchmark comparison
The successful backtest-run response and backtest-detail response SHALL expose an ordered collection containing both benchmark keys, names, five metrics, and strategy-minus-benchmark total-return and annualized-return differences. The detail response SHALL additionally expose ordered benchmark net-value curve points; legacy persisted runs SHALL return an empty collection rather than synthetic benchmark values.

#### Scenario: New backtest API response has two benchmarks
- **WHEN** a client runs or reads a newly completed benchmark-enabled backtest
- **THEN** the response contains `equal_weight_monthly` and `csi_300_buy_hold` exactly once
- **AND** each entry contains all five metrics and both relative-return differences

#### Scenario: Detail exposes benchmark curves
- **WHEN** a client requests the detail of a benchmark-enabled backtest
- **THEN** each benchmark entry includes net-value points ordered by trade date

#### Scenario: Legacy detail remains readable
- **WHEN** a client requests a persisted run with no benchmark records
- **THEN** the detail response succeeds with an empty benchmark collection

### Requirement: Backtest responses expose persisted expanded risk metrics
Successful backtest-run and backtest-detail responses SHALL expose strategy Sortino, Calmar and longest drawdown duration fields. Every benchmark entry SHALL expose its own Sortino, Calmar and duration fields plus strategy-relative Tracking Error and Information Ratio. Decimal values SHALL remain strings, duration counts SHALL be integers, dates SHALL be ISO dates, and unavailable values SHALL be null.

#### Scenario: New detail exposes strategy and dual-benchmark metrics
- **WHEN** a client reads a newly completed benchmark-enabled backtest
- **THEN** the strategy response contains the persisted Sortino, Calmar and duration fields
- **AND** each fixed benchmark contains its persisted downside, duration, TE and IR fields

#### Scenario: Legacy detail returns explicit nulls
- **WHEN** a client reads a run created before expanded metric support
- **THEN** the response succeeds
- **AND** all expanded strategy and benchmark fields are null rather than dynamically recalculated

### Requirement: Backtest responses expose stored benchmark-regime metrics
Benchmark entries in successful run and detail responses SHALL expose nullable CAPM Alpha, Beta, R-squared, daily CAPM observation count, Monthly Up Capture, selected up-month count, Monthly Down Capture, and selected down-month count. CAPM values SHALL be non-null only for `csi_300_buy_hold`; capture values remain available for both fixed benchmarks, Decimal values SHALL remain six-place strings, and the router MUST NOT recalculate them.

#### Scenario: New detail returns exact persisted comparison values
- **WHEN** Backtest Detail loads a newly calculated benchmark-enabled run
- **THEN** both named benchmark objects return their stored monthly capture values and selected-month counts
- **AND** only the CSI 300 object returns stored proxy CAPM values and count

#### Scenario: Legacy detail retains explicit nulls
- **WHEN** Backtest Detail loads legacy benchmark rows created before this Change
- **THEN** new fields are null rather than omitted, zero-filled, or recalculated

### Requirement: Walk-forward responses expose versioned regime evidence
Walk-forward detail SHALL serialize validated `wf_evidence_v2` per-window and aggregate benchmark-regime evidence with metric-local counts and statuses, while valid legacy `wf_evidence_v1` detail remains readable without fabricated fields. OpenAPI SHALL describe both supported evidence shapes unambiguously.

#### Scenario: V2 detail preserves evidence semantics
- **WHEN** a client requests a valid `wf_evidence_v2` history
- **THEN** the response returns named proxy/monthly-capture metrics, daily-session and selected-month evidence counts, aggregate counts, and statuses unchanged

#### Scenario: Invalid evidence has no partial response
- **WHEN** persisted v2 evidence fails strict validation
- **THEN** the endpoint returns the standard error envelope and no partial Walk-forward detail

### Requirement: Backtest Detail exposes derived return stability
`GET /api/backtests/{run_id}` SHALL include required `return_stability` metadata plus strategy and ordered fixed-benchmark rolling/monthly/yearly series derived by the shared core capability. Decimal values SHALL be six-place strings; dates/periods, counts, requested-scope partial flags, rolling status, and Sharpe status SHALL be typed explicitly. The router MUST NOT recalculate financial values.

#### Scenario: Detail returns exact core-derived series
- **WHEN** a persisted benchmark-enabled run has valid curves and sufficient observations
- **THEN** the response contains strategy and both benchmark series in stable benchmark order
- **AND** every value, date, count, status, and partial flag equals the core result

#### Scenario: Empty or short curve returns explicit empty state
- **WHEN** a valid run has an empty curve or fewer than 64 points
- **THEN** the response returns the appropriate typed status and empty rolling array
- **AND** does not fabricate zeros or omit the required stability object

#### Scenario: Corrupt curve has no partial detail
- **WHEN** persisted strategy or benchmark curve evidence violates the stability contract
- **THEN** the endpoint returns the standard error envelope and no partial Backtest Detail

### Requirement: Other backtest payloads remain unchanged
Backtest list and run-creation responses SHALL NOT include return-stability series, and the detail endpoint SHALL derive them only for the requested run without mutating or duplicating persisted data.

#### Scenario: List response remains bounded
- **WHEN** a client requests the backtest list after this Change
- **THEN** its existing item schema and curve-loading behavior remain unchanged

### Requirement: Backtest responses expose stored distribution-risk evidence
Successful backtest-run and detail responses SHALL expose nullable Historical VaR 95%, Historical CVaR 95%, Skewness, Excess Kurtosis, effective observation count, tail observation count, and derived `sufficient`/`insufficient_evidence` status for the strategy and each fixed benchmark. Decimal values SHALL be six-place strings, routers MUST NOT recompute metrics, and legacy null counts SHALL produce an explicit unavailable legacy status rather than an assumed zero sample.

#### Scenario: New response preserves stored values and positive-loss sign
- **WHEN** a newly calculated benchmark-enabled run is serialized
- **THEN** strategy and both benchmark objects return exact stored metrics/counts and derived statuses
- **AND** returned VaR/CVaR values satisfy the positive-loss invariant

#### Scenario: Legacy response does not fabricate evidence
- **WHEN** a legacy run or benchmark has null distribution fields and counts
- **THEN** new metric fields remain null with an explicit legacy-unavailable status

### Requirement: Walk-forward Detail exposes validated v3 distribution evidence
Walk-forward Detail SHALL serialize validated `wf_evidence_v3` per-window and aggregate distribution groups with named owners, metric-local counts, and statuses. Valid v1/v2 detail SHALL remain readable according to its version, and OpenAPI SHALL distinguish supported shapes without browser inference.

#### Scenario: V3 response matches validated history
- **WHEN** a client requests a valid v3 Walk-forward history
- **THEN** every distribution value, count, null, status, and owner matches the validated evidence document

#### Scenario: Invalid v3 returns no partial detail
- **WHEN** persisted v3 evidence violates its strict contract
- **THEN** the endpoint returns the standard error envelope and no partial Walk-forward response

### Requirement: API triggers Walk-forward run asynchronously
The API service SHALL expose `POST /api/walk-forwards/run` with no request body and no query parameters. The endpoint SHALL load the walk-forward configuration path from the lifespan application configuration (MVP fixed to `config/walk_forward_v1.yaml`), execute `WalkForwardRunner.run()` off the event loop via `asyncio.to_thread`, and return HTTP 202 with a JSON body containing the positive `walk_forward_run_id` of a `WalkForwardRun` row whose `status` is `running`. The endpoint SHALL NOT block on completion of the run, SHALL NOT accept a client-supplied configuration path or file content, and SHALL NOT start a second run when the configured strategy already has a `running` record that is not stale. Expected domain failures (missing configuration, empty trading calendar, insufficient prices, no scorable combinations) SHALL use the existing typed domain error mapping with `validation` or `operation_failed` category; unexpected exceptions SHALL use the standard unexpected-error contract.

#### Scenario: Accepted run returns running identity
- **WHEN** a client posts to `/api/walk-forwards/run` against a database with sufficient market data and a valid walk-forward configuration
- **THEN** the response status is 202
- **AND** the response body contains a positive `walk_forward_run_id`
- **AND** a `WalkForwardRun` row with that id exists with `status = "running"` and a non-null `started_at`

#### Scenario: Missing market data returns structured error
- **WHEN** a client posts to `/api/walk-forwards/run` and the configured range has no local market prices
- **THEN** the response status is 400
- **AND** the response body uses the stable API error shape with category `operation_failed`
- **AND** no `WalkForwardRun` row with `status = "running"` is left persisted

#### Scenario: Client-supplied config path is rejected
- **WHEN** a client posts to `/api/walk-forwards/run?configPath=/etc/passwd` or supplies a config path in the request body
- **THEN** the response status is 422 or 400
- **AND** the response body uses the stable API error shape with category `validation`
- **AND** no walk-forward execution is started

#### Scenario: Concurrent run against non-stale running record is rejected
- **WHEN** a client posts to `/api/walk-forwards/run` while a current-strategy `WalkForwardRun` with `status = "running"` and `started_at` less than one hour ago already exists
- **THEN** the response status is 409
- **AND** the response body uses the stable API error shape with category `operation_failed`
- **AND** no second walk-forward execution is started

### Requirement: Walk-forward list and detail responses expose run status
`GET /api/walk-forwards` summary items and `GET /api/walk-forwards/{run_id}` run metadata SHALL include `status` (`running`, `success`, or `failed`) and nullable `error_message`. The list endpoint SHALL continue to scope by current `strategy_id`, retain stable `finished_at DESC, run_id DESC` ordering, and `running` records (with null `finished_at`) SHALL sort before any completed record by `started_at DESC`. Detail of a `running` record SHALL return complete metadata with null `finished_at`, empty `windows`, and the placeholder `evidence_version`/`evidence_json` written at start; Detail of a `failed` record SHALL return `error_message` and null `finished_at` only when the runner could not set it, otherwise the runner-set `finished_at`. Unknown and other-strategy ids SHALL use the standard 404 contract.

#### Scenario: Running record appears in list with status
- **WHEN** a `WalkForwardRun` with `status = "running"` exists for the current strategy
- **THEN** the list response includes that run with `status = "running"` and null `finished_at`
- **AND** it sorts before any completed run

#### Scenario: Failed record detail exposes error message
- **WHEN** a client requests the detail of a `WalkForwardRun` with `status = "failed"`
- **THEN** the response status is 200
- **AND** the run metadata includes `status = "failed"` and the persisted `error_message`
- **AND** `windows` is empty and `evidence` reflects the placeholder written at start

#### Scenario: Legacy success record backfilled by migration
- **WHEN** a client requests a `WalkForwardRun` persisted before this Change
- **THEN** the response metadata includes `status = "success"` and null `error_message`
- **AND** existing detail fields, windows, and evidence remain unchanged


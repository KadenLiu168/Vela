## ADDED Requirements

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

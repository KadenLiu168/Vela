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
The API service SHALL keep strategy and data-processing behavior in `vela_core` and SHALL NOT duplicate strategy logic in the API application skeleton.

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
The API service SHALL expose database session wiring for future routes without adding business API endpoints in this change.

#### Scenario: API endpoint surface remains minimal
- **WHEN** a developer inspects the API routes after database wiring is added
- **THEN** no strategy, market data, signal, or backtest endpoint has been added by this change

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


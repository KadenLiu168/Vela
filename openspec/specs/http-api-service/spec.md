# http-api-service Specification

## Purpose
Defines the FastAPI service surface, including the local-development `POST /api/setup/bootstrap` endpoint and startup strategy-config caching.
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

### Requirement: API caches loaded strategy config
The API service SHALL load the strategy configuration once at startup and store it on the FastAPI application state so multiple request handlers can reuse it without re-reading the YAML from disk.

#### Scenario: Strategy config is loaded at startup
- **WHEN** the API application starts
- **THEN** the application state exposes a `strategy_config` attribute containing the loaded strategy configuration

#### Scenario: Multiple request handlers reuse cached config
- **WHEN** the `GET /api/config` and `POST /api/setup/bootstrap` endpoints run during the same API process lifetime
- **THEN** both endpoints observe the same `strategy_config` instance loaded at startup
- **AND** neither endpoint re-reads the strategy config YAML from disk on each request

### Requirement: API strategy signal list endpoint
The API service SHALL expose `GET /api/strategy-signals` returning a paginated list of successful strategy signal summaries scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns filtered summaries
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** the response status is 200
- **AND** the response body includes a `signals` array of summaries whose `strategy_id` and `config_version` match the current strategy config
- **AND** only `success`-status signals are included
- **AND** summaries are ordered by `generated_at` descending then `id` descending

#### Scenario: Endpoint honors limit and offset
- **WHEN** a client requests `GET /api/strategy-signals?limit=20&offset=40`
- **THEN** the response contains at most 20 summaries starting at offset 40

#### Scenario: Empty history returns empty array
- **WHEN** a client requests `GET /api/strategy-signals` and no successful signal exists for the current strategy and version
- **THEN** the response body's `signals` array is empty

### Requirement: API strategy signal detail endpoint
The API service SHALL expose `GET /api/strategy-signals/{signal_id}` returning the metadata and target positions of one strategy signal by id, scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns signal detail
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an existing id that belongs to the current strategy and version
- **THEN** the response status is 200
- **AND** the response body includes the signal metadata and a `positions` array

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


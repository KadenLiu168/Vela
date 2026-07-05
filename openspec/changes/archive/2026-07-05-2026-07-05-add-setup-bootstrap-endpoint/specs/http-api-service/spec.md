## ADDED Requirements

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

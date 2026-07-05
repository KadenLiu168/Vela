## ADDED Requirements

### Requirement: Run compound local setup bootstrap
The system SHALL provide a `run_local_setup_bootstrap` orchestration function that runs the existing `init-db`, `sync-etf-pool`, and full market data fetch workflows in order.

#### Scenario: All three steps succeed
- **WHEN** a caller invokes `run_local_setup_bootstrap` against an empty local database with a valid strategy config and a working market data provider
- **THEN** the function applies Alembic migrations to the current head revision
- **AND** synchronizes the configured ETF pool into `etf_info`
- **AND** runs a full market data fetch for all active ETFs
- **AND** returns a `BootstrapResult` with `status = "success"`

#### Scenario: First step succeeds and second step fails
- **WHEN** a caller invokes `run_local_setup_bootstrap` against a database where Alembic migrations succeed but the configured ETF pool is missing or invalid
- **THEN** the function stops before running the full market data fetch step
- **AND** returns a `BootstrapResult` with `status = "failed"` and `failed_step = "sync_etf_pool"`
- **AND** the recorded `migrate` step result still reports `status = "success"`

#### Scenario: First two steps succeed and third step fails
- **WHEN** a caller invokes `run_local_setup_bootstrap` against an initialized database where the market data provider raises an unrecoverable error
- **THEN** the function records both `migrate` and `sync_etf_pool` step results as `status = "success"`
- **AND** records the `fetch_full_market_data` step result as `status = "failed"`
- **AND** returns a `BootstrapResult` with `status = "failed"` and `failed_step = "fetch_full_market_data"`

#### Scenario: Re-run against already-initialized database
- **WHEN** a caller invokes `run_local_setup_bootstrap` against a database that is already at the current Alembic head and already has the configured ETF pool synchronized
- **THEN** the `migrate` step reports `status = "success"` without altering schema
- **AND** the `sync_etf_pool` step reports `status = "success"` with `unchanged` equal to the active ETF count
- **AND** the `fetch_full_market_data` step still runs to completion

### Requirement: Per-step status reporting
The system SHALL report the status, duration, and step-specific result fields for every step the bootstrap orchestrator runs.

#### Scenario: Inspect per-step status
- **WHEN** a caller inspects the `steps` list of a `BootstrapResult`
- **THEN** each entry has a `name` of `"migrate"`, `"sync_etf_pool"`, or `"fetch_full_market_data"`
- **AND** each entry has a `status` of `"success"` or `"failed"`
- **AND** each entry has a `duration_seconds` field expressed as a float
- **AND** each entry has an optional `error_message` populated when `status = "failed"`

#### Scenario: Inspect aggregate bootstrap result
- **WHEN** a caller inspects a `BootstrapResult`
- **THEN** the top-level `status` is `"success"` only when every step has `status = "success"`
- **AND** `failed_step` is the name of the first step with `status = "failed"` or `null` when all steps succeeded
- **AND** `total_duration_seconds` is the sum of the per-step durations

### Requirement: HTTP endpoint for local setup bootstrap
The system SHALL expose a `POST /api/setup/bootstrap` endpoint that invokes the core `run_local_setup_bootstrap` orchestration and returns the `BootstrapResult` to the caller.

#### Scenario: Endpoint returns success aggregate
- **WHEN** a client posts to `/api/setup/bootstrap` against an empty local database
- **THEN** the response status is 200
- **AND** the response body is a JSON object with `status = "success"`, three `steps` entries each with `status = "success"`, and `failed_step = null`

#### Scenario: Endpoint reports step failure without 5xx
- **WHEN** a client posts to `/api/setup/bootstrap` and a non-first step fails for a known business reason
- **THEN** the response status is 200
- **AND** the response body is a JSON object with `status = "failed"`, `failed_step` set to the failing step name, and the failing step's `error_message` populated

#### Scenario: Endpoint uses cached strategy config
- **WHEN** a client posts to `/api/setup/bootstrap` after the API has loaded the strategy config
- **THEN** the endpoint uses the loaded strategy config cached in API application state
- **AND** the endpoint does not re-read the strategy config YAML from disk

### Requirement: Local development scope
The system SHALL document the bootstrap endpoint as local-development only and SHALL NOT use it to mutate schema in shared or production databases.

#### Scenario: Endpoint scoped to local development
- **WHEN** a developer reads the documentation for `POST /api/setup/bootstrap`
- **THEN** the documentation states that the endpoint is intended for local development setup only
- **AND** the documentation states that production database migrations must continue to use the `vela init-db` CLI command

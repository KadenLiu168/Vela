## MODIFIED Requirements

### Requirement: HTTP endpoint for local setup bootstrap
The system SHALL expose a `POST /api/setup/bootstrap` endpoint that loads one current `AppConfig` from disk at the start of each request, passes that request-scoped config to the core `run_local_setup_bootstrap` orchestration, and returns the `BootstrapResult` to the caller.

#### Scenario: Endpoint returns success aggregate
- **WHEN** a client posts to `/api/setup/bootstrap` against an empty local database
- **THEN** the response status is 200
- **AND** the response body is a JSON object with `status = "success"`, three `steps` entries each with `status = "success"`, and `failed_step = null`

#### Scenario: Endpoint reports step failure without 5xx
- **WHEN** a client posts to `/api/setup/bootstrap` and a non-first step fails for a known business reason
- **THEN** the response status is 200
- **AND** the response body is a JSON object with `status = "failed"`, `failed_step` set to the failing step name, and the failing step's `error_message` populated

#### Scenario: Endpoint reads current strategy config
- **WHEN** two bootstrap requests run in the same API process and the resolved config changes between them
- **THEN** the endpoint calls `load_app_config` once at the start of each request
- **AND** each orchestration receives the `AppConfig` loaded for its own request
- **AND** the second request does not reuse the first request's config from API application state

#### Scenario: Current ETF pool is used by bootstrap
- **WHEN** a client posts to `/api/setup/bootstrap` after editing the ETF-pool config resolved from `config/strategy_v1.yaml`, without restarting the API
- **THEN** the synchronized `etf_info` rows reflect the configured entries and field values read for that request

#### Scenario: Invalid current config prevents orchestration
- **WHEN** the current strategy or ETF-pool config cannot be read, parsed, or validated
- **THEN** the endpoint returns status 500 using the stable API error envelope with code `config_error` and category `operation_failed`
- **AND** `run_local_setup_bootstrap` is not invoked

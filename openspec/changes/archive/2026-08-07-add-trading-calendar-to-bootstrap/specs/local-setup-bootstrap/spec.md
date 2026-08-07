## MODIFIED Requirements

### Requirement: Run compound local setup bootstrap
The system SHALL provide a `run_local_setup_bootstrap` orchestration function that runs the existing `init-db`, `sync-etf-pool`, trading-calendar sync, and full market-data fetch workflows in order: `migrate` → `sync_etf_pool` → `sync_trading_calendar` → `fetch_full_market_data`. The trading-calendar step SHALL invoke the existing `sync_trading_calendar_to_db` workflow with default arguments.

#### Scenario: All four steps succeed
- **WHEN** a caller invokes `run_local_setup_bootstrap` against an empty local database with a valid strategy config and a working market data provider
- **THEN** the function applies Alembic migrations to the current head revision
- **AND** synchronizes the configured ETF pool into `etf_info`
- **AND** synchronizes A-share trading days into `trading_calendar`
- **AND** runs a full market data fetch for all active ETFs
- **AND** returns a `BootstrapResult` with `status = "success"`

#### Scenario: First step succeeds and second step fails
- **WHEN** a caller invokes `run_local_setup_bootstrap` against a database where Alembic migrations succeed but the configured ETF pool is missing or invalid
- **THEN** the function stops before running the trading-calendar sync or the full market data fetch step
- **AND** returns a `BootstrapResult` with `status = "failed"` and `failed_step = "sync_etf_pool"`
- **AND** the recorded `migrate` step result still reports `status = "success"`

#### Scenario: First two steps succeed and fourth step fails
- **WHEN** a caller invokes `run_local_setup_bootstrap` against an initialized database where the market data provider raises an unrecoverable error
- **THEN** the function records the `migrate`, `sync_etf_pool`, and `sync_trading_calendar` step results as `status = "success"`
- **AND** records the `fetch_full_market_data` step result as `status = "failed"`
- **AND** returns a `BootstrapResult` with `status = "failed"` and `failed_step = "fetch_full_market_data"`

#### Scenario: Re-run against already-initialized database
- **WHEN** a caller invokes `run_local_setup_bootstrap` against a database that is already at the current Alembic head, already has the configured ETF pool synchronized, and already has trading days synchronized
- **THEN** the `migrate` step reports `status = "success"` without altering schema
- **AND** the `sync_etf_pool` step reports `status = "success"` with `unchanged` equal to the active ETF count
- **AND** the `sync_trading_calendar` step reports `status = "success"` with updated count equal to the existing trading-day count
- **AND** the `fetch_full_market_data` step still runs to completion

### Requirement: Per-step status reporting
The system SHALL report the status, duration, and step-specific result fields for every step the bootstrap orchestrator runs.

#### Scenario: Inspect per-step status
- **WHEN** a caller inspects the `steps` list of a `BootstrapResult`
- **THEN** each entry has a `name` of `"migrate"`, `"sync_etf_pool"`, `"sync_trading_calendar"`, or `"fetch_full_market_data"`
- **AND** each entry has a `status` of `"success"` or `"failed"`
- **AND** each entry has a `duration_seconds` field expressed as a float
- **AND** each entry has an optional `error_message` populated when `status = "failed"`

#### Scenario: Inspect aggregate bootstrap result
- **WHEN** a caller inspects a `BootstrapResult`
- **THEN** the top-level `status` is `"success"` only when every step has `status = "success"`
- **AND** `failed_step` is the name of the first step with `status = "failed"` or `null` when all steps succeeded
- **AND** `total_duration_seconds` is the sum of the per-step durations

### Requirement: HTTP endpoint for local setup bootstrap
The system SHALL expose a `POST /api/setup/bootstrap` endpoint that loads one current `AppConfig` from disk at the start of each request, passes that request-scoped config to the core `run_local_setup_bootstrap` orchestration, and returns the `BootstrapResult` to the caller.

#### Scenario: Endpoint returns success aggregate
- **WHEN** a client posts to `/api/setup/bootstrap` against an empty local database
- **THEN** the response status is 200
- **AND** the response body is a JSON object with `status = "success"`, four `steps` entries each with `status = "success"`, and `failed_step = null`

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

### Requirement: Caller-provided script location for bootstrap
The system SHALL require callers of `run_local_setup_bootstrap` to provide `script_location` explicitly. The function SHALL NOT compute a default script location from a hardcoded project-relative path.

#### Scenario: Caller omits script_location
- **WHEN** a caller invokes `run_local_setup_bootstrap` without the `script_location` argument
- **THEN** the function raises a `TypeError` (missing required keyword argument)
- **AND** no Alembic migration is attempted

#### Scenario: API endpoint passes script_location explicitly
- **WHEN** a client posts to `POST /api/setup/bootstrap`
- **THEN** the endpoint passes an explicit `script_location` derived from the app-layer project root to `run_local_setup_bootstrap`
- **AND** the endpoint does not rely on a default value computed inside `vela_core`

#### Scenario: Bootstrap still runs four steps in order
- **WHEN** a caller invokes `run_local_setup_bootstrap` with all required arguments including `script_location`
- **THEN** the function applies Alembic migrations via `vela_core.migration.run_alembic_upgrade`
- **AND** synchronizes the configured ETF pool
- **AND** synchronizes the trading calendar via `vela_core.trading_calendar_sync.sync_trading_calendar_to_db`
- **AND** runs a full market data fetch
- **AND** returns a `BootstrapResult` with per-step status

## ADDED Requirements

### Requirement: Calendar sync failure does not block market data fetch
The bootstrap trading-calendar step SHALL detect failure by inspecting the returned `TradingCalendarSyncResult.status` rather than by catching an exception, because `sync_trading_calendar_to_db` returns `status = "failed"` with an error message on akshare fetch, parse, or empty-result failures instead of raising. When the calendar step fails, the orchestrator SHALL record the step as `status = "failed"` with the error message, SHALL NOT short-circuit, and SHALL continue to the `fetch_full_market_data` step. The overall `BootstrapResult.status` SHALL remain `"failed"` with `failed_step = "sync_trading_calendar"`.

#### Scenario: Calendar sync failure does not prevent market data fetch
- **WHEN** a caller invokes `run_local_setup_bootstrap` and the akshare trading-calendar source raises an exception or returns no trade dates
- **THEN** the `sync_trading_calendar` step result has `status = "failed"` and a populated `error_message`
- **AND** the `fetch_full_market_data` step still executes and records its own status
- **AND** the returned `BootstrapResult` has `status = "failed"` and `failed_step = "sync_trading_calendar"`
- **AND** the `migrate` and `sync_etf_pool` step results still report `status = "success"`

#### Scenario: Calendar sync success populates trading calendar
- **WHEN** a caller invokes `run_local_setup_bootstrap` against a database whose `trading_calendar` table is empty and the akshare source returns trade dates
- **THEN** the `sync_trading_calendar` step result has `status = "success"`
- **AND** the `trading_calendar` table contains at least one row after bootstrap completes
- **AND** a subsequent Walk-Forward preflight that requires sessions in the configured range no longer fails with `official trading calendar has no sessions in configured range`

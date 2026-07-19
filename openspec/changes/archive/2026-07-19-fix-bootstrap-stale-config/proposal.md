## Why

The `POST /api/setup/bootstrap` endpoint reads the strategy/ETF-pool config from `app.state.strategy_config`, a copy frozen once at API process startup (`apps/api/src/vela_api/main.py:49`). Every other config-consuming endpoint (`/api/config`, `/api/dashboard`, `/api/strategy-signals/generate`) reads the YAML from disk on every request. As a result, when a developer edits `config/etf_pool.yaml` (the only config Bootstrap persists — into `etf_info`) and clicks Bootstrap **without restarting the API**, the edit is silently ignored: the DB keeps the startup-time values. This inconsistency is confusing and contradicts the project's expectation that config edits take effect without a restart.

## What Changes

- Remove the startup-time frozen config cache `app.state.strategy_config` set in `main.py:49`.
- Change the `POST /api/setup/bootstrap` handler (`main.py:158`) to call `load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)` once at the start of every request and pass that request-scoped `AppConfig` to `run_local_setup_bootstrap`, matching the live-read behavior of the other config-consuming endpoints.
- Modify the `local-setup-bootstrap` spec to replace the cached-config scenario with request-scoped live loading and to define the existing `ConfigError` HTTP behavior for an unreadable, malformed, or invalid config.
- Modify the `http-api-service` spec to remove the obsolete requirement that the API cache strategy config in application state. That requirement directly conflicts with this change and already overstates the current implementation: `GET /api/config` reads through `get_config_summary()` on each request rather than using `app.state.strategy_config`.
- Update the endpoint tests to inject config through `vela_api.main.load_app_config`, prove two successive requests can receive different `AppConfig` values, and prove config-load failure returns the stable `config_error` response without starting bootstrap orchestration.

No new endpoints, no schema changes, no breaking API contract change for clients (response shape is unchanged).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `local-setup-bootstrap`: the "HTTP endpoint for local setup bootstrap" requirement is modified — its "Endpoint uses cached strategy config" scenario is removed and a "Endpoint reads current strategy config" scenario is added, so the endpoint SHALL read the current strategy config from disk on each request and config edits take effect without an API restart.
- `http-api-service`: the obsolete "API caches loaded strategy config" requirement is removed because no request handler will use a startup-frozen `AppConfig` after this change.

## Impact

- **Code**: `apps/api/src/vela_api/main.py` (remove `app.state.strategy_config` assignment; change `setup_bootstrap` to live-load config).
- **Tests**: `apps/api/tests/test_bootstrap_endpoint.py` — three tests that inject config via `app.state.strategy_config` move to a `load_app_config` monkeypatch; focused assertions cover per-request reload and config-load failure.
- **Behavior**: Bootstrap now reflects the latest `config/strategy_v1.yaml` + `config/etf_pool.yaml` without requiring an API restart. The `~1 minute` commit-after-fetch timing and TablePlus non-auto-refresh caveats are unrelated and unchanged.
- **Startup/error timing**: invalid config no longer prevents `vela_api.main` from importing solely because of the removed cache initialization. Bootstrap instead loads and validates config before orchestration and returns the API's existing HTTP 500 `config_error` envelope if loading fails; no bootstrap step runs in that case.
- **Dependencies**: none added; `load_app_config` and `DEFAULT_STRATEGY_CONFIG_PATH` already imported in `main.py`.

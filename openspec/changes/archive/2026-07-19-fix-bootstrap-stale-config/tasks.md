## 1. Fix the Bootstrap config loading

- [x] 1.1 In `apps/api/src/vela_api/main.py`, delete `app.state.strategy_config = load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)` so no startup-frozen config copy is kept.
- [x] 1.2 In `setup_bootstrap`, call `load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)` exactly once before invoking `run_local_setup_bootstrap`, and pass that request-scoped value as `app_config`.
- [x] 1.3 Confirm there are no remaining source references to `app.state.strategy_config`. Keep config loading in the API layer; do not change `run_local_setup_bootstrap`, `sync_etf_pool_to_db`, config models, response serialization, or database schema.

## 2. Update tests

- [x] 2.1 Change the success and step-failure endpoint tests to accept `monkeypatch` and replace their `app.state.strategy_config` assignment/reset with a monkeypatch of `vela_api.main.load_app_config` returning the one-ETF test `AppConfig`. Keep the tests hermetic and preserve their existing response assertions.
- [x] 2.2 Replace `test_bootstrap_endpoint_uses_cached_config` with a focused per-request reload test: make `load_app_config` return two distinguishable configs in sequence, issue two requests in one API process, capture the `app_config` values passed to a monkeypatched `run_local_setup_bootstrap`, and assert the first and second request receive the first and second configs respectively.
- [x] 2.3 In the per-request reload test, assert `load_app_config` is called exactly once per request with `DEFAULT_STRATEGY_CONFIG_PATH`, and do not set `app.state.strategy_config`. Avoid editing checked-in YAML or running full provider/database bootstrap work in this focused wiring test.
- [x] 2.4 Add a config failure test that makes `load_app_config` raise `ConfigError`, sends the request with `raise_server_exceptions=False`, asserts the existing HTTP 500 error envelope (`code = "config_error"`, `category = "operation_failed"`), and asserts `run_local_setup_bootstrap` was not called.

## 3. Validate

- [x] 3.1 Run `uv run pytest apps/api/tests/test_bootstrap_endpoint.py apps/api/tests/test_api_config.py apps/api/tests/test_api_errors.py packages/core/tests/test_config.py`; all pass.
- [x] 3.2 Run `uv run ruff check apps/api/src/vela_api/main.py apps/api/tests/test_bootstrap_endpoint.py` and `uv run mypy apps/api/src/vela_api/main.py`; both pass.
- [x] 3.3 Confirm the implementation diff is limited to `apps/api/src/vela_api/main.py` and `apps/api/tests/test_bootstrap_endpoint.py`, with no changes to checked-in config, database schema/migrations, core bootstrap orchestration, or API response types.

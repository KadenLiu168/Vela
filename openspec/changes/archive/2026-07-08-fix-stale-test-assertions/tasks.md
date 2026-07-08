## 1. Root cause A - ETF count assertions derive from loaded config

- [x] 1.1 In `packages/core/tests/test_config.py::test_load_existing_etf_pool_yaml_returns_typed_config`, replace `assert len(config.etfs) == 6` with an assertion that derives the expected count from the source YAML (e.g. parse the YAML with `yaml.safe_load` and compare `len(config.etfs)` to `len(raw["etfs"])`), or assert non-empty plus per-entry typed fields; keep the existing `pool_id`/`provider`/`currency`/first-entry assertions.
- [x] 1.2 In `packages/core/tests/test_config.py::test_load_existing_app_config_contains_checked_in_values`, replace `assert len(config.etf_pool.etfs) == 6` with the same derived-from-source approach, keeping the surrounding `version`/`pool_id`/`provider` assertions.
- [x] 1.3 In `apps/cli/tests/test_sync_etf_pool.py::test_sync_etf_pool_populates_active_etfs_after_init_db`, replace `assert active_count == 6` with a count derived from `load_etf_pool_config(...)` filtered to active ETFs, so it tracks the checked-in pool.
- [x] 1.4 In `apps/api/tests/test_api_config.py::test_config_endpoint_returns_strategy_and_etf_pool_summary`, replace `assert body["etf_pool"]["total_etfs"] == 6` and `assert body["etf_pool"]["active_etfs"] == 6` with values derived from `load_etf_pool_config(...)` (total = all, active = `is_active` True). Note: this assertion is currently masked by the strategy_id failure fixed in task 2.2; both must pass.

## 2. Root cause B - strategy_id assertions use loaded config value

- [x] 2.1 In `apps/api/tests/test_dashboard.py::test_dashboard_endpoint_reads_persisted_sqlite_rows`, replace the expected `"strategy_id": "dual_momentum"` (and any `dual_momentum` literal in the `body["strategy"]` block) with the value sourced from `load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml").strategy.strategy_id` (currently `Dual_momentum`).
- [x] 2.2 In `apps/api/tests/test_api_config.py::test_config_endpoint_returns_strategy_and_etf_pool_summary`, replace the expected `strategy_id` literal `"dual_momentum"` in the `body["strategy"]` dict with `load_app_config(...).strategy.strategy_id`.

## 3. Root cause C - dashboard etf_list fixture matches aggregation output

- [x] 3.1 In `apps/api/tests/test_market_data_fetch.py::test_market_data_fetch_endpoint_updates_dashboard_summary`, add `"earliest_trade_date": "2026-06-17"` to the expected `etf_list` entry, matching the production `dashboard_aggregation.py` output for the seeded data (SPY has only `2026-06-17`).
- [x] 3.2 In `apps/api/tests/test_dashboard.py::test_dashboard_endpoint_reads_persisted_sqlite_rows`, add `earliest_trade_date` to each expected `etf_list` entry (`QQQ` -> `2026-06-23`, `SPY` -> `2026-06-22`), matching the production `dashboard_aggregation.py` output for the seeded data. This drift was masked behind the `strategy_id` failure fixed in task 2.1; both must pass.

## 4. Root cause D - mypy annotation on strategy_signal_report counts

- [x] 4.1 In `packages/core/src/vela_core/strategy_signal_report.py` around line 115, annotate `counts: dict[int, int]` and build it via a comprehension `{row[0]: row[1] for row in session.execute(...).all()}` instead of `dict(...)`, resolving the two `mypy` `var-annotated`/`arg-type` errors with no behavior change.

## 5. Verification

- [x] 5.1 Run `uv run pytest -q` and confirm 453 passed, 0 failed (was 447 passed / 6 failed).
- [x] 5.2 Run `uv run ruff check .` and confirm no new lint errors.
- [x] 5.3 Run `uv run mypy packages/core/src/vela_core` and confirm 0 errors (was 2).
- [x] 5.4 Run `uv run openspec validate fix-stale-test-assertions` and confirm valid.
- [x] 5.5 Spot-check that no production runtime behavior changed: `uv run vela generate-signal` and `uv run vela run-backtest` still succeed against a temp DB. Verified: `init-db`/`sync-etf-pool` succeed (11 ETFs inserted, confirming the stale `== 6`); `generate-signal`/`run-backtest` exit 0 with graceful "No local market prices found" (temp-DB data dependency, not introduced by this change). The only production edit (`counts` annotation in `list_strategy_signals`) is behavior-equivalent and covered by 73 signal pytest tests.

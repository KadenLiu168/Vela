## 1. Confirm Regression Protection

- [x] 1.1 Review `packages/core/tests/test_database.py` and the nine named CLI test modules to map existing coverage across all ten affected helpers, including successful results, propagated failures, and configuration/document loading behavior.
- [x] 1.2 Add at most one focused CLI-local observable-behavior test only if the coverage review finds a real consolidation gap; do not duplicate core commit/rollback/close tests or bind the test to a private helper name or incidental call count.

## 2. Consolidate CLI Session Composition

- [x] 2.1 Add one private context-managed helper in `apps/cli/src/vela_cli/main.py` that composes `create_engine_from_url(database_url)`, `create_session_factory(engine)`, and the existing `managed_session(session_factory)`, yielding its session without implementing transaction policy, caching, reuse, or disposal.
- [x] 2.2 Migrate `fetch_full_market_data`, `fetch_incremental_market_data`, `sync_etf_pool`, `sync_etf_session_status`, and `sync_trading_calendar` to the private helper while preserving their business calls, results, and intentional errors.
- [x] 2.3 Migrate `generate_signal`, `export_signal_report`, `run_backtest`, `run_walk_forward`, and `export_backtest_report` to the private helper while keeping configuration/document preparation outside the managed-session context.
- [x] 2.4 Search the final CLI wiring to confirm the ten helpers no longer repeat the full composition and that `init-db`, `walk-forward-worker`, core public APIs, and API initialization/request lifecycle are unchanged.

## 3. Verify Behavior and Scope

- [x] 3.1 Run `uv run pytest packages/core/tests/test_database.py apps/cli/tests/test_fetch_market_data.py apps/cli/tests/test_sync_etf_pool.py apps/cli/tests/test_sync_etf_session_status.py apps/cli/tests/test_sync_trading_calendar.py apps/cli/tests/test_generate_signal.py apps/cli/tests/test_export_signal_report.py apps/cli/tests/test_run_backtest.py apps/cli/tests/test_export_backtest_report.py apps/cli/tests/test_walk_forward.py` using only test-owned `tmp_path` or explicit temporary databases; do not invoke commands against repository-root `vela.db`.
- [x] 3.2 Run the full Python gate: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 3.3 Run `openspec validate consolidate-cli-session-lifecycle --strict` and `git diff --check`; verify the final diff is limited to this Change's artifacts, the private CLI composition refactor, and any strictly necessary focused test, with no persistent database, API, schema, migration, model, config-schema, Web, Linear, archive, commit, or push changes.

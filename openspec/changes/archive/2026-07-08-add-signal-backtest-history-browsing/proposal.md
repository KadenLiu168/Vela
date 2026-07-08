## Why

The web frontend's "Latest Signal" and "Backtest Detail" pages only expose the single most recent signal/backtest, even though the database already preserves every historical run (360 strategy signals, multiple backtest runs). Users cannot inspect prior signals or backtests from the UI. The routing layer already reserves `/signals/:id` and `/backtests/:id`, and `BacktestDetailPage` already accepts a `backtestId` prop, but `SignalDetailPage` ignores its `signalId` prop and always calls the latest-only API, there is no list page on either side, and `strategy_signal` rows do not persist `strategy_id` so history cannot be scoped to a strategy. The existing `backtest_run.strategy_name` column stores a `strategy_id` value under a misleading name and has mixed casing (`Dual_momentum` / `dual_momentum`), which would break strict equality filtering.

## What Changes

- Add a `strategy_id` column to `strategy_signal` (Alembic migration + backfill of existing 360 rows with the current strategy id) and write it on every persist.
- Rename `backtest_run.strategy_name` to `strategy_id` in the same migration and normalize its casing to the current `config.strategy_id` (collapsing `dual_momentum` → `Dual_momentum`); propagate the rename across model, core, API, and web layers.
- Add core query helpers: list strategy signals by `strategy_id + config_version + status=success` with limit/offset, and fetch a strategy signal report by id (pure-by-id, no strategy filter).
- Add API endpoints `GET /api/strategy-signals` (list, filtered) and `GET /api/strategy-signals/{signal_id}` (detail); extend `GET /api/backtests` with `strategy_id` + `config_version` filtering (defaulting to the current strategy) and `offset`.
- Enforce the current `strategy_id + config_version` on detail endpoints: signal and backtest detail fetch by id at the core layer, then the API layer returns 404 when the row's `strategy_id`/`config_version` do not match the current config. Core helpers stay pure-by-id so the CLI is unaffected.
- Add web list pages at `/signals` and `/backtests` (paginated tables of historical runs) and convert `/signals/:id` and `/backtests/:id` detail pages to fetch by id; replace the dead `/signals/demo-signal` nav entry.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-signal-model`: add `strategy_id` column; add list and by-id query helpers; persist `strategy_id` on generation.
- `backtest-run-model`: rename `strategy_name` column to `strategy_id` across model, persistence, and report contracts.
- `http-api-service`: add strategy signal list and detail endpoints; add (and extend) the backtest list and detail endpoints with strategy/version filtering, 404-on-foreign-strategy, and offset.
- `web-frontend-app`: add signal and backtest history list pages; switch detail pages to id-based fetching; update routes and nav.
- `database-migrations`: add a migration revision that adds the `strategy_id` column to `strategy_signal`, renames `backtest_run.strategy_name` to `strategy_id`, backfills/normalizes values, and enforces non-null.

## Impact

- Database: one new Alembic revision adding a `String` column to `strategy_signal` (backfill 360 rows) and renaming `backtest_run.strategy_name` → `strategy_id` with casing normalization; local `vela.db` is migrated on next `alembic upgrade`.
- Core package: new query helpers in `strategy_signal_report.py` (list + by-id) reusing the existing `_to_report` mapper; `persist_strategy_signal` gains a `strategy_id` parameter; `BacktestRun.strategy_name`, `BacktestRunResult.strategy_name`, and `DashboardBacktestSummary.strategy_name` are renamed to `strategy_id` across `models/backtest.py`, `backtest_result_persistence.py`, `backtest_runner.py`, `backtest_report.py`, and `dashboard_aggregation.py`.
- API: two new GET endpoints, the backtest list endpoint extended (filter + offset), and both detail endpoints now 404 on foreign strategy; response fields `strategy_name` become `strategy_id` in backtest detail and dashboard backtest summary.
- Web frontend: two new page components, route table changes, nav label/path changes, new API client functions; `strategy_name` → `strategy_id` in client types and `BacktestDetailPage`; `SignalDetailPage` stops ignoring `signalId`.
- Tests: core query helper tests, API contract tests for new/extended endpoints and foreign-strategy 404, web page tests for list/detail navigation, migration test for column rename + backfill + normalization; existing backtest/dashboard tests updated for the renamed field.
- Specs: updates five capability specs.

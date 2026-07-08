## 1. Database Migration

- [x] 1.1 Add Alembic revision that adds a nullable `strategy_id` column to `strategy_signal`.
- [x] 1.2 Backfill all existing `strategy_signal` rows with the current `config.strategy_id` value.
- [x] 1.3 Enforce `strategy_id` non-null (alter column or table rebuild as SQLite requires).
- [x] 1.4 In the same revision, rename `backtest_run.strategy_name` to `strategy_id` and normalize its casing to the current `config.strategy_id` (`dual_momentum` → `Dual_momentum`); rebuild the `ix_backtest_run_strategy_config` index if needed.
- [x] 1.5 Add migration test asserting empty-DB upgrade succeeds and existing-DB column rename + backfill + normalization are correct.

## 2. Core Layer

- [x] 2.1 Add `strategy_id` field to the `StrategySignal` model.
- [x] 2.2 Rename `BacktestRun.strategy_name` to `strategy_id` (column + index).
- [x] 2.3 Update `persist_strategy_signal` to accept and write `strategy_id`.
- [x] 2.4 Update `generate_strategy_signal` call sites to pass `config.strategy_id`.
- [x] 2.5 Rename `strategy_name` → `strategy_id` in `BacktestRunResult` (`backtest_result_persistence.py`), `backtest_runner.py` (write site), `backtest_report.py` (report output), and `DashboardBacktestSummary` (`dashboard_aggregation.py`).
- [x] 2.6 Add `list_strategy_signals(session, *, strategy_id, config_version, limit, offset)` returning lightweight summary rows (success only).
- [x] 2.7 Add `get_strategy_signal_report(session, *, signal_id)` returning a `StrategySignalReport` (reuse `_to_report`); return `None` when not found. Stays pure-by-id (no strategy filter).
- [x] 2.8 Add core unit tests for list (filtering, ordering, limit/offset) and by-id (found / not found).

## 3. API Layer

- [x] 3.1 Add `GET /api/strategy-signals` with `limit`/`offset` query params, filtered by current `strategy_id + version + success`, ordered by `generated_at desc, id desc`.
- [x] 3.2 Add `GET /api/strategy-signals/{signal_id}` returning detail (metadata + positions); fetch by id then 404 when the row's `strategy_id`/`config_version` do not match the current config; 404 when not found.
- [x] 3.3 Extend `GET /api/backtests` with optional `strategy_id`/`config_version` filter (defaulting to current) and `offset` param; keep `limit`; expose `strategy_id` + `config_version` in each list item.
- [x] 3.4 Enforce current `strategy_id`/`config_version` on `GET /api/backtests/{run_id}`: fetch by id then 404 on mismatch or missing.
- [x] 3.5 Rename `strategy_name` → `strategy_id` in backtest detail and dashboard backtest summary responses.
- [x] 3.6 Add API contract tests for both new endpoints, the extended backtest list (filtering, offset, shape), and foreign-strategy 404 on both detail endpoints.

## 4. Web Frontend

- [x] 4.1 Add `listStrategySignals` and `getStrategySignalDetail` API client functions; extend `listBacktests` with `offset` and optional strategy filter.
- [x] 4.2 Rename `strategy_name` → `strategy_id` in `BacktestDetailRun` and `DashboardBacktestSummary` client types; update `BacktestDetailPage` usage.
- [x] 4.3 Add `SignalListPage` rendering a paginated table of historical signals with a link per row to `/signals/:id`.
- [x] 4.4 Add `BacktestListPage` rendering a paginated table of historical backtests with a link per row to `/backtests/:id`.
- [x] 4.5 Rework `SignalDetailPage` to fetch by `signalId` via the by-id endpoint (stop ignoring the prop); render a not-found state on 404.
- [x] 4.6 Rework `BacktestDetailPage` so `/backtests` (no id) shows the list page instead of the latest-detail fallback; `/backtests/:id` keeps fetching by id; render a not-found state on 404.
- [x] 4.7 Update route table: `/signals` → list, `/signals/:id` → detail, `/backtests` → list, `/backtests/:id` → detail.
- [x] 4.8 Update nav: rename "Latest Signal" → "Signals" pointing to `/signals`, "Backtest Detail" → "Backtests" pointing to `/backtests`; drop the dead `/signals/demo-signal`.
- [x] 4.9 Add web tests covering list rendering, row navigation, detail-by-id fetching, foreign/not-found states, and empty states.

## 5. Verification

- [x] 5.1 Run `uv run pytest packages/core/tests`.
- [x] 5.2 Run `uv run pytest apps/api/tests`.
- [x] 5.3 Run web tests (`npm test` in `apps/web`).
- [x] 5.4 Run `uv run alembic upgrade head` against a fresh and an existing local DB.
- [x] 5.5 Run `uv run ruff check .` and format checks.
- [x] 5.6 Run OpenSpec validation for `add-signal-backtest-history-browsing`.

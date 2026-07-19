## Why

The web Signals page lists every strategy signal, but the `strategy_signal` table stores no provenance. Signals are written by two distinct paths — live single-date generation (`generate_and_persist_strategy_signal`, reached via the dashboard "Generate" button, the CLI, and (eventually) external cron jobs) and backtest batch generation (`run_backtest` → `generate_historical_strategy_signals`). Both paths call `persist_strategy_signal` with the same fields and **no source marker and no link back to the originating backtest run**.

As a result, a user cannot tell whether a given signal was produced by a manual Generate click, an automated/scheduled call, or a backtest run — and there is no way to navigate from a signal back to the backtest run that produced it, or from a backtest run to the signals it produced. The `is_fallback` flag already present in list/detail responses is a different axis (defensive-fallback selection) and does not address provenance.

## What Changes

- Add provenance to the `strategy_signal` model: a constrained `source` column (`manual`, `scheduled`, `backtest`, plus a `legacy` value used only for rows backfilled by the migration) and a nullable `backtest_run_id` foreign key to `backtest_run`.
- Update `persist_strategy_signal` to accept `source` and an optional `backtest_run_id`.
- Update the live generation path so callers can supply `source` (default `manual`); the HTTP generate endpoint and CLI gain an optional `source` query/flag so automated callers can label themselves `scheduled`. No scheduler is built — `scheduled` is a caller-supplied label only.
- Update `run_backtest` to capture the signal ids it produces; persist each backtest signal with `source="backtest"` and `backtest_run_id=None`, then after the `backtest_run` row is created, write the `backtest_run_id` onto exactly those signals in the same caller-managed transaction (the minimal-change approach; signals are already persisted before the run row exists).
- Surface provenance in the API: list/detail responses include `source` and `backtest_run_id`; the backtest detail response includes its signal ids; the generate response includes `source`.
- Surface provenance in the web UI: the Signals list gains a "Source" column (badge); the Signal detail shows the source and, for backtest signals, a link to `/backtests/{run_id}`; the `BacktestDetailPage` (`/backtests/{id}`) lists the signals produced by that run.
- Add an Alembic migration that adds the two columns and backfills existing rows.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `strategy-signal-model`: The `strategy_signal` table SHALL carry a `source` discriminator and a nullable `backtest_run_id` foreign key, persisted for every signal so live and backtest-generated signals are distinguishable and linkable.
- `strategy-signal-generation`: The core persistence helper and the live/backtest generation orchestration SHALL record `source` (and `backtest_run_id` for backtest signals) on every persisted signal.
- `backtest-execution`: A backtest SHALL link every signal it persists to the newly created run atomically and SHALL fail rather than commit a partially linked run.
- `backtest-run-model`: `BacktestRun` SHALL expose its linked signals in deterministic signal-date/id order, and the persisted-result query SHALL load them for the detail API.
- `http-api-service`: The signal list, signal detail, signal generate, and backtest detail endpoints SHALL expose provenance fields and (for generate) accept a caller-supplied `source`.
- `cli-database-initialization`: The `generate-signal` CLI command SHALL accept `--source {manual,scheduled}`, default it to `manual`, and forward it to the shared core service.
- `web-frontend-app`: The Signals list, Signal detail, and backtest detail views SHALL display signal provenance and provide navigation between a signal and its backtest run.

## Impact

- Affected code:
  - `packages/core/src/vela_core/models/strategy_signal.py` (new columns + relationship).
  - `packages/core/src/vela_core/models/backtest.py` (ordered `signals` relationship).
  - `packages/core/src/vela_core/strategy_signal_persistence.py` (`persist_strategy_signal` signature).
  - `packages/core/src/vela_core/strategy_signal_service.py` (live path `source` passthrough) and a new core helper `link_signals_to_backtest_run` (post-run backtest linkage).
  - `packages/core/src/vela_core/backtest_runner.py` (capture signal ids, link after run create).
  - `packages/core/src/vela_core/backtest_result_persistence.py` (load linked signals with persisted backtest detail).
  - `packages/core/src/vela_core/strategy_signal_report.py` (`StrategySignalListEntry` / `StrategySignalReport` add `source` + `backtest_run_id`).
  - `apps/api/src/vela_api/main.py` (endpoint params, response builders).
  - `apps/cli/src/vela_cli/main.py` (optional `--source` flag on generate).
  - `apps/web/src/pages/SignalListPage.tsx`, `SignalDetailPage.tsx`, and `BacktestDetailPage.tsx` (source column/badges + backtest link).
  - `apps/web/src/api/client.ts` (types + `source` query param).
- Affected tests:
  - Migration/model: legacy backfill, constraints/FK/indexes, downgrade/re-upgrade, and ordered relationships.
  - Core: persistence validation/recording, exact backtest linkage, and transaction rollback.
  - API/CLI: list/detail/generate/backtest-detail provenance contracts, invalid-source no-write behavior, and CLI forwarding.
  - Web: API-client source handling, all Source badges, bidirectional links, and empty linked-signal state.
- Database migration: new Alembic revision adding constrained `source` (non-null after backfill) and nullable, indexed `backtest_run_id`.
- No new external dependencies. Scheduler/automation is explicitly out of scope.

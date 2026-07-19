## 1. Database migration and ORM model

- [x] 1.1 Add failing model tests for `StrategySignal.source`/`backtest_run_id`, the named four-value source and non-backtest-link check constraints, the `backtest_run_id` index/FK, and the bidirectional ordered `StrategySignal.backtest_run` / `BacktestRun.signals` relationships.
- [x] 1.2 Create the next Alembic revision after the current head. Add nullable `source`, backfill every existing signal to `source='legacy'`, then use one SQLite-compatible batch rebuild to make `source` non-null, add nullable `backtest_run_id` with its FK, and add `ck_strategy_signal_source` plus `ck_strategy_signal_backtest_link`; add `ix_strategy_signal_backtest_run_id` afterward. Do not rely on post-`ALTER TABLE ADD COLUMN` FK creation and do not add a speculative standalone source index.
- [x] 1.3 Implement the migration downgrade in dependency-safe order so the index, check/FK metadata, and columns are removed cleanly.
- [x] 1.4 Add `StrategySignal.SOURCES`, runtime-writable source constants, the two mapped columns, both named check constraints, the index, and nullable `backtest_run` relationship; add the ordered `BacktestRun.signals` relationship (`signal_date`, then `id`).
- [x] 1.5 Add a migration test that upgrades a database at the previous revision containing pre-existing signals and runs, then asserts `source='legacy'`, `backtest_run_id IS NULL`, non-null/check/FK metadata, and the expected index.
- [x] 1.6 Extend migration verification to cover downgrade/re-upgrade and keep `compare_metadata(..., Base.metadata) == []` at head.

## 2. Core persistence and live generation

- [x] 2.1 Add failing persistence/service tests for stored `source`/`backtest_run_id`, default `manual`, explicit `scheduled`, and rejection of `legacy`, `backtest` on the live service, unknown runtime values, and manual/scheduled rows with a non-null backtest link before a row is added.
- [x] 2.2 Update `persist_strategy_signal` to require `source`, accept optional `backtest_run_id`, validate runtime source as `manual`/`scheduled`/`backtest`, reject non-backtest sources with a non-null link, and write both values.
- [x] 2.3 Update `generate_and_persist_strategy_signal` to accept `source="manual"`, restrict it to `manual`/`scheduled`, and pass it through with `backtest_run_id=None`; preserve its existing commit and result semantics.
- [x] 2.4 Use repository-wide searches to update every direct `persist_strategy_signal(...)` test caller and every direct `StrategySignal(...)` fixture/constructor affected by the new non-null field, including core, API, dashboard, and shared integration fixtures. Do not silently add a model default that would hide missing provenance in production code.

## 3. Backtest linkage and transaction integrity

- [x] 3.1 Add failing helper/runner tests proving a completed run links all and only its generated signals, including failed generated signals, in signal-date/id order and leaves unrelated/manual/already-linked signals untouched.
- [x] 3.2 Add `link_signals_to_backtest_run(session, run_id, signal_ids: Sequence[int])`: de-duplicate ids, no-op on empty input, update only matching unlinked rows with `source="backtest"`, set only `backtest_run_id`, and raise when affected-row count differs from the distinct id count.
- [x] 3.3 In `run_backtest`, persist callback rows with `source="backtest"`/`backtest_run_id=None`, require every generation result to contain an id, persist the run, and invoke the link helper with the captured ids.
- [x] 3.4 Keep signal rows, run/curve rows, and linkage in the existing caller-managed transaction: do not add a commit to `run_backtest` or the link helper. Add a managed-session rollback test for a missing id or link mismatch so no partial run, curve, signal, or link commits.
- [x] 3.5 Update `get_backtest_result` to `selectinload` both ordered `equity_curve` and ordered `signals`; extend core query/relationship tests.

## 4. HTTP API

- [x] 4.1 Add failing API tests for generate default/explicit source, persisted-source equality, and HTTP 400 stable error responses with no persisted row for `backtest`, `legacy`, and unknown values.
- [x] 4.2 Add a string `source` query parameter to `POST /api/strategy-signals/generate`, default it to `manual`, validate it manually as `manual`/`scheduled` to preserve HTTP 400 (not FastAPI 422), pass it to core, and echo the validated value in the additive response field.
- [x] 4.3 Add `source` and `backtest_run_id` to `StrategySignalListEntry` and `StrategySignalReport`, populate them from the already loaded `StrategySignal`, and include them in list/detail response builders without changing existing filtering, ordering, or pagination.
- [x] 4.4 Add top-level `signal_ids` and `signal_count` to backtest detail from `run.signals`, preserving signal-date/id order and returning `[]`/`0` for a run with no linked signals.
- [x] 4.5 Update exact API response assertions and shared API fixtures for signal list/detail/generate and backtest detail, including the end-to-end run→detail linkage loop.

## 5. CLI

- [x] 5.1 Add failing CLI tests for the default `manual` value, explicit `--source scheduled` forwarding/persistence, and argparse rejection of `backtest`, `legacy`, and unknown values before core is called.
- [x] 5.2 Add `--source {manual,scheduled}` (default `manual`) to `generate-signal` and forward it through the CLI wrapper to the shared core service; keep all other output and exit-status behavior unchanged.

## 6. Web frontend

- [x] 6.1 Define shared frontend `StrategySignalSource` (`manual | scheduled | backtest | legacy`) and `LiveStrategySignalSource` (`manual | scheduled`) unions; extend generation/list/detail response types with provenance and extend top-level `BacktestDetailResponse` with `signal_ids`/`signal_count`.
- [x] 6.2 Update `generateStrategySignal(source?: LiveStrategySignalSource)` so omitted source keeps the existing URL and relies on the API's `manual` default, while an explicit value is encoded in the query string; keep Dashboard/command-palette calls unchanged and add API-client tests for omitted and scheduled URLs.
- [x] 6.3 Add a Source column to `SignalListPage` and render accessible, existing-token-based badges for all four values, including a clear "predates provenance tracking" label or tooltip for `legacy`.
- [x] 6.4 Show source on `SignalDetailPage`; render `/backtests/{backtest_run_id}` only when source is `backtest` and the id is non-null, with no link for manual/scheduled/legacy rows.
- [x] 6.5 Show `signal_count` and list every `signal_id` as a `/signals/{signal_id}` link on `BacktestDetailPage`; render an explicit empty state for zero linked signals.
- [x] 6.6 Update web fixtures and add render tests for all source badges, backtest-link presence/absence, ordered backtest signal links/count, and the empty-linked-signals state.

## 7. Verification

- [x] 7.1 Run targeted migration/model/persistence/service/backtest/report tests, then the complete Python suite.
- [x] 7.2 Run API and CLI provenance contract tests, including invalid-input/no-write and run→signal bidirectional navigation cases.
- [x] 7.3 Run frontend lint, CSS lint, typecheck, tests, and build.
- [x] 7.4 Run Python `ruff check`, `ruff format --check`, and `mypy` using the repository CI commands.
- [x] 7.5 Run `openspec validate add-signal-provenance --strict` and `openspec status --change add-signal-provenance --json`; confirm all planning artifacts remain complete and all implementation tasks are checked only after their verification passes.

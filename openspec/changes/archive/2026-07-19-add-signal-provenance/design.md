## Context

`strategy_signal` rows are written by two paths that today produce indistinguishable rows:

- **Live**: `generate_and_persist_strategy_signal` (reached from the dashboard Generate action, the CLI, and external automation), producing a single signal for the latest (or an explicit) date.
- **Backtest**: `run_backtest` → `generate_historical_strategy_signals`, producing one signal per rebalance date across a date range.

`persist_strategy_signal` writes only `strategy_id`, `signal_date`, `config_version`, `generated_at`, `status`, `result`, `error_message`, and positions. There is no `source` and no link to the `backtest_run` that produced a signal. `BacktestRun` has no relationship to `StrategySignal` either. So provenance is lost at write time, and the UI cannot distinguish or navigate.

The `is_fallback` flag in list/detail responses is unrelated: it marks positions chosen by defensive fallback (`rank is None and score is None`), an output-quality axis, not an origin axis.

We are explicitly **not** building a scheduler. `scheduled` is only a caller-supplied label so that external automation can tag its live-signal calls differently from a human click.

## Goals / Non-Goals

**Goals:**

- Make every persisted signal carry a `source` discriminator (`manual`, `scheduled`, `backtest`; a `legacy` value is reserved for migration backfill and is never written by live code).
- Link backtest-generated signals to their `backtest_run` via a nullable `backtest_run_id`, enabling bidirectional navigation.
- Expose provenance through the HTTP API and the web UI without breaking existing response contracts beyond the additive new fields.
- Backfill existing rows so the column is immediately meaningful.

**Non-Goals:**

- Do not build a scheduler, cron, or any automation engine. `scheduled` is a label only.
- Do not change strategy calculation, momentum scoring, trend filtering, defensive fallback, or target-weight semantics.
- Do not change the meaning of `is_fallback`.
- Do not change the existing pagination, ordering, or scoping of the signal/backtest endpoints.

## Decisions

### Add provenance columns to `StrategySignal`

Add two columns and two check constraints:

- `source: Mapped[str] = mapped_column(String(16), nullable=False)` — one of `manual`, `scheduled`, `backtest`, or migration-only `legacy`. Non-null after backfill.
- `backtest_run_id: Mapped[int | None]` — FK to `backtest_run.id`, nullable (only set for `backtest` source).
- `ck_strategy_signal_source` — database check restricting `source` to the four stored values.
- `ck_strategy_signal_backtest_link` — database check requiring `backtest_run_id IS NULL` whenever `source` is not `backtest`. A backtest source may be temporarily null inside the run transaction until post-run linkage.

Add an ORM relationship `backtest_run` on `StrategySignal` (nullable, `back_populates="signals"`) and `signals` on `BacktestRun` (back-populates `backtest_run`), so the backtest detail API can load a run's signals via the ORM (ordered by `signal_date` then `id`). Add `ix_strategy_signal_backtest_run_id` for the relationship lookup.

Rationale:

- A single discriminator column plus a nullable FK is the minimal schema that supports both "label the source" and "navigate to the run".
- Keeping `backtest_run_id` nullable (rather than routing everything through a join table) matches the existing `BacktestEquityCurve.backtest_run_id` style already in the codebase.
- A named database check makes the stored-value invariant true even for direct ORM/SQL writes. Runtime persistence still rejects `legacy`; only the migration writes it.
- The link-consistency check prevents a manual, scheduled, or legacy row from pointing at a backtest while still permitting the chosen two-stage backtest insert/link flow.
- There is no source-filtering API in this change, and `source` has very low cardinality, so a standalone source index would be speculative. It can be added later with an actual filtering requirement.

Alternatives considered:

- A separate `signal_generation_log` table with richer metadata: rejected — overkill for the current need; the two columns cover labeling and navigation.
- Two booleans `is_backtest` / `is_scheduled`: rejected — conflates orthogonal flags and makes "manual" implicit; an enum is clearer and extensible.

### `persist_strategy_signal` gains `source` and optional `backtest_run_id`

Signature becomes:

```python
def persist_strategy_signal(
    session: Session,
    *,
    strategy_id: str,
    signal_date: date,
    config_version: str,
    generated_at: datetime,
    status: str,
    result: str | None,
    positions: Sequence[StrategySignalPositionInput],
    source: str,
    backtest_run_id: int | None = None,
    error_message: str | None = None,
) -> StrategySignalPersistenceResult:
    ...
```

Rationale:

- The persistence helper is the single choke point for every signal write (live + backtest), so adding the fields here forces both callers to supply provenance.
- The helper validates runtime sources as exactly `manual`, `scheduled`, or `backtest` and raises before adding a row for `legacy` or an unknown value. It also rejects a non-null `backtest_run_id` for `manual` or `scheduled`. `legacy` remains a database value only for migration-backfilled rows.

### Live path: caller-supplied `source`, default `manual`

`generate_and_persist_strategy_signal(session, *, config, signal_date=None, source="manual")` passes `source` through to `persist_strategy_signal` and leaves `backtest_run_id=None`.

- The HTTP `POST /api/strategy-signals/generate` gains an optional query param `source` (allowed values `manual`, `scheduled`; default `manual`). It validates the value manually and raises `HTTPException(status_code=400)` for disallowed values. Do not rely on FastAPI `Query` enum validation, which would return 422 and diverge from the existing `operation_failed` error shape used by the missing-market-data case.
- The CLI `generate-signal` gains an optional `--source {manual,scheduled}` flag (default `manual`).
- The core live service also rejects any value outside `manual`/`scheduled`, so direct Python callers cannot label a live signal as `backtest` or `legacy`.

Note: the generate endpoint returns `source` in its response by **echoing the validated request param**. The pure `GenerateStrategySignalResult` returned by `generate_and_persist_strategy_signal` intentionally does NOT carry `source` (source is a persistence concern, not a calculation result), so the endpoint supplies `source` from the request rather than from the result object. The `GET /api/strategy-signals/latest` endpoint is out of scope for this change; if the Dashboard "Latest signal" panel should show provenance, add `source`/`backtest_run_id` there in a follow-up.

Rationale:

- Keeping the default `manual` preserves current behavior for the dashboard button and human CLI use with zero changes to those callers.
- Restricting the generate endpoint to `manual`/`scheduled` (excluding `backtest`) prevents a live endpoint from impersonating a backtest.

### Backtest path: capture ids, link after run creation (minimal-change)

`run_backtest` currently persists all signals **before** the `backtest_run` row is created (see `backtest_runner.py` lines ~157 vs ~189). Rather than reorder the whole run, do the following:

- At persist time, the backtest's `_persist_signal` callback already knows these are backtest signals, so it calls `persist_strategy_signal(..., source="backtest", backtest_run_id=None)`. The `source` column is satisfied at write time; `backtest_run_id` is unknown until the run row exists, so it stays `NULL` here.
- After `persist_backtest_result` creates the `backtest_run` row and returns its id, collect the `strategy_signal_id` values returned by `generate_historical_strategy_signals` and issue one bulk `UPDATE strategy_signal SET backtest_run_id=:run_id WHERE id IN (:signal_ids)` to attach them to the run. `source` is already `backtest`, so the UPDATE only needs to set `backtest_run_id`.

Implementation options considered:

- **Chosen**: persist with `source="backtest"` + `backtest_run_id=None`, then a post-run bulk UPDATE that sets only `backtest_run_id`. Lowest risk; keeps the existing run-creation order and metrics computation intact.
- Create the `backtest_run` first in `running` state, thread `backtest_run_id` through `_persist_signal`, then update to final status. More "correct" (signals know their run immediately) but requires reordering run creation ahead of signal generation and threading the id through the pure generation callback signature — larger blast radius for little benefit.

A small core helper (e.g. `link_signals_to_backtest_run(session, run_id, signal_ids)`) keeps the UPDATE logic testable and out of `backtest_runner`'s hot path. `run_backtest` first requires every generation result to contain a persisted id; a missing id raises rather than producing a partially traceable run. The helper de-duplicates the integer ids, treats an empty input as a no-op, updates only rows with those ids plus `source="backtest"` and `backtest_run_id IS NULL`, and verifies that the affected-row count equals the number of distinct ids. A mismatch raises.

The generated signals, backtest run, curve rows, and linkage remain in the same caller-managed SQLAlchemy transaction. Neither `run_backtest` nor the linkage helper commits. The existing API and CLI `managed_session` boundary therefore commits all four pieces together or rolls all of them back when id capture/linkage fails. Primary-key predicates plus the `backtest_run_id IS NULL` precondition prevent repeated or concurrent runs from cross-linking or reassigning rows.

### Backfill existing rows in the migration

Existing `strategy_signal` rows predate provenance. The migration:

1. Adds `source` as nullable initially.
2. Backfills `source` to `'legacy'` for all existing rows. (`'legacy'` is a stable value outside the live/backtest enum so it is unambiguous that the row predates provenance tracking.)
3. Uses one SQLite-compatible Alembic batch rebuild to alter `source` to `NOT NULL`, add nullable `backtest_run_id` with its foreign key, and add the named source/link-consistency check constraints. This avoids relying on SQLite to add a foreign-key constraint after `ALTER TABLE ADD COLUMN`.
4. Adds `ix_strategy_signal_backtest_run_id`.

Rationale:

- A heuristic that tries to reattach old signals to historical `backtest_run` rows via `generated_at`/`started_at` equality is fragile (two runs could share a timestamp; manual generates could collide) and the payoff is low because old backtests are experiments. Uniform `'legacy'` is honest and simple.
- `backtest_run_id` stays nullable for legacy rows (no run to link).

### API surface additions (additive)

- `GET /api/strategy-signals` list item gains `source` and `backtest_run_id`.
- `GET /api/strategy-signals/{signal_id}` detail gains `source` and `backtest_run_id`.
- `POST /api/strategy-signals/generate` request gains optional `source`; response gains `source`.
- `GET /api/backtests/{run_id}` detail gains top-level `signal_ids` (ordered by `signal_date` then `id`) and `signal_count`; `get_backtest_result` select-in-loads the ordered relationship alongside `equity_curve`.

All additions are new fields; existing fields and status codes are unchanged.

### Web UI additions

- `SignalListPage`: add a "Source" column rendering a badge — `manual` (neutral), `scheduled` (info), `backtest` (accent), `legacy` (muted).
- `SignalDetailPage`: show `source` and `generated_at`; when `source == backtest` and `backtest_run_id` is present, render a link to `/backtests/{backtest_run_id}`.
- `BacktestDetailPage` (`/backtests/{id}` route): show `signal_count` and list the run's `signal_ids` as links into `/signals/{signal_id}`; render an explicit empty state when the array is empty. A filtered Signals-list alternative is not used because the current list API has no `backtest_run_id` filter.
- The shared web client accepts an optional live source. When omitted, it keeps the existing `/strategy-signals/generate` URL and relies on the API's `manual` default; when `scheduled` is explicitly supplied, it appends `?source=scheduled`.

## Risks / Trade-offs

- [Risk] Post-run linkage could be incomplete if `generate_historical_strategy_signals` unexpectedly returns a result whose `strategy_signal_id` is `None`, or if an id does not identify an unlinked backtest signal. → Mitigation: fail fast on a missing id, require an exact affected-row count, and let the managed-session boundary roll back the entire run.
- [Risk] Adding a non-null `source` column requires backfill in the same migration; a failure mid-migration leaves the column nullable. → Mitigation: backfill before the NOT NULL alter; test the migration against a DB with pre-existing signals.
- [Risk] `'legacy'` value could confuse users. → Mitigation: document it as "predates provenance tracking" in the UI tooltip/label and in the spec.
- [Risk] Changing `persist_strategy_signal`'s signature breaks many direct test callers and fixtures, not just the two production callers. → Mitigation: use repository-wide call-site searches and update core tests, API/integration fixtures, and direct `StrategySignal(...)` constructors together.
- [Risk] The local database is SQLite (`vela.db`). Adding `NOT NULL`/check/FK metadata cannot rely on PostgreSQL-style `ALTER TABLE` operations. → Mitigation: add/backfill nullable `source` first, then use one `batch_alter_table("strategy_signal")` rebuild for the NOT NULL alteration, nullable FK column, and both checks.
- [Risk] SQLite does not enforce foreign keys unless `PRAGMA foreign_keys=ON` is set per connection. → Mitigation: this matches the existing `backtest_equity_curve.backtest_run_id` FK behavior; no new enforcement is introduced.
- [Trade-off] `scheduled` is asserted by the caller, not verified against a scheduler identity. This is intentional because the application has no scheduler or authentication layer in scope.
- [Trade-off] The existing latest-signal/dashboard queries continue to consider successful backtest signals, and `GET /api/strategy-signals/latest` does not expose provenance in this change. Changing latest-signal semantics is a separate product decision and is intentionally not bundled here.
- [Trade-off] Backtest detail links every persisted signal, including failed signals. The existing Signal detail contract does not expose status/error metadata, so a failed signal remains less explanatory than a successful one; enriching failure detail is useful follow-up work but is not required to establish provenance.

## Migration Plan

1. Alembic revision: add/backfill `source`, then batch-add its NOT NULL rule, both check constraints, and the nullable `backtest_run_id` FK; index `backtest_run_id`.
2. Update `StrategySignal` model + `BacktestRun` relationship.
3. Update `persist_strategy_signal` signature; update both callers.
4. Add `source` passthrough to live path + API/CLI params.
5. Add exact-count backtest linkage helper + wire it into `run_backtest` without adding a commit.
6. Update the persisted-backtest query to load ordered signals.
7. Update report/entry dataclasses (`source`, `backtest_run_id`) and API response builders.
8. Update web client types + Signal list/detail + backtest detail rendering.
9. Add/adjust migration, model, core, API, CLI, integration-fixture, and web tests.
10. Run the repository quality gates and OpenSpec validation.

Rollback after deployment: run Alembic downgrade to the previous revision before reverting the implementation. The downgrade removes the relationship index, check/FK metadata, and both columns, so provenance and backtest-signal links written after upgrade are intentionally lost. Code and schema must be rolled back together.

## Open Questions

- None blocking. The `legacy` backfill strategy and the post-run UPDATE linking approach are the recommended resolutions and can proceed as described.

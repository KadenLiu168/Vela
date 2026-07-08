## Context

The database already preserves every signal and backtest run, but the UI only surfaces the latest. The routing layer half-implements id-based viewing: `/signals/:id` and `/backtests/:id` routes exist, `BacktestDetailPage` honors a `backtestId` prop, but `SignalDetailPage` accepts `signalId` and ignores it (always calling `/api/strategy-signals/latest`), and the nav entry points at the dead string `/signals/demo-signal`. On the data side, `strategy_signal` persists only `config_version` (= `config.version`, e.g. "v1") and never persists `config.strategy_id` (e.g. "Dual_momentum"), so history cannot be scoped to a strategy. `backtest_run` does store the strategy id but in a column mislabeled `strategy_name`, with mixed casing (`Dual_momentum` and `dual_momentum`) from an earlier config change, which would break strict equality filtering.

## Goals / Non-Goals

**Goals:**

- Let users browse and open any historical successful signal and any historical backtest for the current strategy from the web UI.
- Scope both list and detail views to the current strategy (`strategy_id + version`) and `success` status; ids belonging to another strategy/version are not reachable from the UI and return 404.
- Persist `strategy_id` on every signal and align the backtest column name to `strategy_id` so the two tables share a consistent strategy identity column.
- Keep signal and backtest browsing UI symmetric (list page + detail page).

**Non-Goals:**

- No multi-strategy support beyond persisting/normalizing `strategy_id`; only the current config's strategy is browsable in the UI for now.
- No dashboard "latest" card deep-links to the newest detail (may be added later).
- No `/signals/latest` or `/backtests/latest` redirect shortcuts (the list page is the entry point).
- No changes to signal generation, backtest execution, scoring, or config schema semantics.
- No rename of the `config_version` column (it remains the `version` landing column; `strategy_id` is added/renamed alongside).
- No change to core query helper signatures (`get_backtest_result`, new `get_strategy_signal_report`) — they stay pure-by-id; strategy enforcement lives in the API layer.

## Decisions

- Add a `strategy_id` `String(64)` non-null column to `strategy_signal` and backfill all existing rows with the current `config.strategy_id`.
  - Rationale: the user requirement is to filter history by `strategy_id + version`; the column does not exist today, so it must be added and populated before any filtered query is meaningful.
  - Alternative considered: filter signal history by `config_version` only. Rejected because it drops `strategy_id` from the stated filter contract and would force a second migration when a second strategy arrives.

- Rename `backtest_run.strategy_name` to `strategy_id` and normalize its casing to the current `config.strategy_id` in the same migration.
  - Rationale: the column stores a strategy id, not a name; renaming aligns it with the new `strategy_signal.strategy_id` so both tables share one identity column name and the same filter contract. Casing normalization collapses `dual_momentum` → `Dual_momentum` so strict equality works and the existing index stays usable.
  - Alternative considered: keep the `strategy_name` name and only normalize casing. Rejected because the misleading name would persist and the two tables would stay asymmetric. Alternative considered: case-insensitive matching with `lower()`. Rejected because it complicates the query, bypasses the index, and leaves dirty data.

- Both list and detail endpoints enforce the current `strategy_id + config_version`. Core query helpers stay pure-by-id; the API layer fetches by id then returns 404 when the row's `strategy_id` or `config_version` does not match the current config.
  - Rationale: the user wants detail views strictly scoped — a foreign-strategy id should not be reviewable from the UI. Putting the check in the API layer keeps `get_backtest_result` and `get_strategy_signal_report` pure-by-id so the CLI (which selects runs by id with no current-strategy context) is unaffected, and avoids changing core helper signatures.
  - Alternative considered: push the strategy filter into the core helpers (passing `strategy_id + version` into `get_backtest_result`/`get_strategy_signal_report`). Rejected because it changes core signatures and breaks CLI consumers that select runs by id without a strategy context.

- Reuse the existing `_to_report` mapper in `strategy_signal_report.py` for the by-id detail path; add `list_strategy_signals` + `get_strategy_signal_report` core helpers.
  - Rationale: `_to_report` already maps a `StrategySignal` ORM row (with positions + ETF join) to the response shape; by-id lookup only needs a different `SELECT` and can share the mapper.
  - Alternative considered: build the detail response inline in the API layer. Rejected because it duplicates the ETF join and position-sorting logic.

- Keep the backtest list query in the API layer (as today), only adding filter parameters and `offset`; do not add a core list helper for backtests.
  - Rationale: the existing `/api/backtests` endpoint already queries `BacktestRun` inline; extracting a core helper for symmetry with signals would be churn without behavioral benefit.
  - Alternative considered: extract a `list_backtest_runs` core helper. Rejected as unnecessary indirection.

- Paginate lists with `limit` + `offset` (not cursor).
  - Rationale: history volume is modest (hundreds of signals, a handful of backtests) and grows slowly (weekly signals); offset pagination is simple, stateless, and good enough.
  - Alternative considered: cursor pagination by `(generated_at, id)`. Rejected as premature.

- Routes become `/signals` (list), `/signals/:id` (detail), `/backtests` (list), `/backtests/:id` (detail). Nav entries become "Signals" → `/signals` and "Backtests" → `/backtests`.
  - Rationale: list page as the canonical entry point matches the chosen UI model (B); the previous `/backtests` = latest-detail convention is replaced.
  - Alternative considered: keep `/backtests` = latest detail and add a separate `/backtests/history` list. Rejected because it splits the mental model and leaves signal/backtest asymmetric.

- The `http-api-service` spec does not currently cover the existing `/api/backtests` list and detail endpoints; this change adds those requirements (in their filtered, paginated, foreign-404 form) rather than modifying them.
  - Rationale: the spec captures target state; the endpoint code is adjusted to match.

## Risks / Trade-offs

- Adding a non-null column on SQLite requires a multi-step migration (add nullable → backfill → enforce non-null, or a table rebuild); the revision must handle this rather than a single `ALTER TABLE ADD COLUMN NOT NULL`.
- Renaming a column on SQLite uses `ALTER TABLE ... RENAME COLUMN` (SQLite 3.25+) or a batch table rebuild; the migration must verify the target SQLite version or use batch mode.
- Backfilling `strategy_id` for 360 existing signal rows assumes they all belong to the current single strategy — true today, but any historical row from a different strategy would be mislabeled; accepted because the DB has only ever run one strategy.
- Renaming `strategy_name` → `strategy_id` is a cross-layer change (~20 references across model, core, API, web, tests); a missed reference surfaces as a test failure, not silent breakage, because the field is exercised end-to-end.
- Strict detail filtering means a direct URL to a foreign-strategy signal/backtest returns 404 — accepted per the user's explicit request; the trade-off is that historical links across strategy migrations will break.
- Offset pagination skews when new rows arrive between page fetches; accepted at current volume.

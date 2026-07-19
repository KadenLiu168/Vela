## Context

`StrategySignal` persists both `strategy_id` and `config_version`, and the current configuration
contains both values (`config/strategy_v1.yaml`: `Dual_momentum`, `v1`). The history list endpoint
already queries by both fields, while detail endpoints fetch by id and reject rows whose two fields
do not match the current config.

Five current query shapes select a latest successful signal:

1. `_get_latest_successful_signal` in `strategy_signal_report.py` powers the core report, HTTP
   latest endpoint, and CLI export; it filters by `config_version + status`.
2. `_get_latest_signal_summary` in `dashboard_aggregation.py` powers the Dashboard; it filters only
   by `status`.
3. `get_latest_successful_strategy_signal` in `strategy_signal_persistence.py` is a public
   exact-date helper; it filters by `signal_date + config_version + status`.
4. `_latest_successful_signals_by_date` in `portfolio_holdings.py` reconstructs holdings for
   backtests; it filters by `config_version + status + date range`.
5. `calculate_strategy_equity_curve` and `run_backtest` reach the fourth query through
   `calculate_portfolio_holdings`.

Because `"v1"` can be reused by another strategy, every shape can select a row belonging to that
other strategy. The report, Dashboard, and portfolio queries are separate SQL implementations, so
one core report regression test cannot prove all paths.

## Goals / Non-Goals

**Goals:**

- Make every current latest-successful signal selection use exact, case-sensitive
  `(strategy_id, config_version)` equality.
- Preserve existing status, optional signal-date, date-range, ordering, id tie-breaker, fallback,
  T+1 holdings, output-shape, and transaction behavior.
- Keep the implementation mechanical: required parameter propagation plus SQL predicates.
- Prove both query behavior and API/CLI/Dashboard/backtest caller wiring with discriminating tests.

**Non-Goals:**

- No normalization or case-folding of strategy ids; persisted identity must match configuration
  exactly.
- No change to signal generation, persistence, provenance, status semantics, or report formatting.
- No attempt to isolate holdings by `source` or `backtest_run_id`; existing same-strategy rerun
  semantics remain unchanged.
- No scoping change to Dashboard `recent_backtest` or market-data/fetch-log summaries.
- No response schema, frontend, database schema, or index change.

## Decisions

### D1 — Require `strategy_id` at every affected public helper boundary

Add a required keyword-only `strategy_id: str` to:

- `get_latest_strategy_signal_report`
- `export_latest_strategy_signal_report`
- `get_latest_successful_strategy_signal`
- `calculate_portfolio_holdings`

Private helpers receive the same explicit value. Existing callers already have a strategy config or
fixture identity, so config loading does not move into core helpers.

This intentionally rejects a backward-compatible default or optional strategy id: falling back to
version-only behavior would preserve the bug and make omission silent.

### D2 — Filter in SQL using exact composite identity

Each affected query adds:

```python
.where(StrategySignal.strategy_id == strategy_id)
.where(StrategySignal.config_version == config_version)
```

The order in which SQLAlchemy receives commutative equality predicates is not a behavioral
requirement. The existing `ix_strategy_signal_strategy_config(strategy_id, config_version)` index
supports this filter; no new schema or index is justified for the local MVP.

Filtering occurs before ordering/limiting. Post-fetch rejection is incorrect for latest queries
because a foreign row could win the limit and hide a valid current-strategy row.

### D3 — Dashboard derives scope from its existing strategy summary

`get_dashboard_summary` reads `strategy_summary["strategy_id"]` and
`strategy_summary["version"]` and passes them into `_get_latest_signal_summary`.
The API already supplies the serialized current strategy config. Missing keys are a programmer
contract violation and may fail fast; adding fallback values or configuration loading inside the
aggregation service would duplicate existing responsibility.

### D4 — Holdings and equity-curve paths propagate the same identity

`calculate_portfolio_holdings` passes `strategy_id` to
`_latest_successful_signals_by_date`. `calculate_strategy_equity_curve` obtains it from its existing
`StrategyConfig`. `run_backtest` passes `config.strategy_id` to its direct holdings call. This
preserves the existing transaction: newly generated signals and subsequent reads remain in the
same caller-managed SQLAlchemy session, with no commit added.

### D5 — Tests must distinguish query behavior from caller wiring

Use a newer successful `Other_strategy/v1` row than the expected `Dual_momentum/v1` row. A
version-only or global-latest implementation then deterministically fails.

Required coverage:

- Core report helper returns the matching strategy and returns `None` when that strategy has no
  success row.
- Public exact-date helper ignores the newer foreign-strategy row.
- Portfolio holdings ignore foreign-strategy rows on the same signal dates, preserving T+1.
- Dashboard aggregation ignores a newer foreign-strategy row.
- API `/latest` ignores a newer foreign-strategy row, proving `config.strategy_id` wiring.
- CLI wrapper forwards the id loaded from its selected config to the export helper.

Existing tests continue to cover status filtering, date filtering, generated-at ordering, id
tie-breaking, fallback detection, response shapes, output formatting, and missing-result behavior.

## Risks / Trade-offs

- **Breaking Python signatures:** four helpers exported from `vela_core` gain a required argument.
  All repository callers and test doubles must be found with a repository-wide symbol search and
  updated together. Unknown external callers must migrate.
- **Observable selection correction:** a database already containing mixed strategies with the
  same version may show a different latest signal or backtest result after the fix. That is the
  intended behavior, not a zero-observable-change guarantee.
- **Case-sensitive identity:** `"Dual_momentum"` and `"dual_momentum"` are distinct. Production
  config and migrated signal rows currently use `"Dual_momentum"`; tests must not hide a mismatch
  by silently changing only expected output.
- **Existing same-strategy backtest mixing remains:** holdings selection still chooses the newest
  successful run per date across sources/runs for one strategy and version. Isolating one backtest
  run would require a separate lifecycle/design change and is not caused by this strategy-id bug.
- **Concurrent inserts:** the existing deterministic `generated_at DESC, id DESC` rule remains.
  Each statement sees the database snapshot provided by its current SQLAlchemy transaction; this
  change adds no multi-statement read-modify-write race.

## Migration Plan

No database migration. Deploy the code and tests together. Rollback is a code revert. Any external
Python consumer must add the new required `strategy_id` keyword before upgrading.

## Open Questions

None.

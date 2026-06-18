## Context

Vela already has SQLAlchemy ORM models for ETF metadata, daily market prices, data fetch logs, and strategy signal runs. Historical backtesting is in Phase 1 scope, but there is not yet a durable model for recording backtest executions or the resulting equity curve.

The model should support future backtest services without assuming a final strategy engine, web UI, broker integration, order execution, or complex portfolio optimization.

## Goals / Non-Goals

**Goals:**

- Define a durable record for each historical backtest run.
- Preserve the parameter snapshot, date range, configuration version, lifecycle status, core metrics, and errors for each run.
- Store equity curve points in a queryable child table associated with a backtest run.
- Keep the model style consistent with the existing SQLAlchemy 2.0 typed ORM models.
- Expose the models through `Base.metadata` for Alembic migration generation.

**Non-Goals:**

- Implement the historical backtest engine or strategy calculation logic.
- Define repository, service-layer, CLI, or API interfaces for running backtests.
- Store trade fills, orders, holdings, benchmark curves, or detailed attribution.
- Enforce all metric and status consistency rules in database constraints.

## Decisions

1. Model `BacktestRun` as an execution run, not a unique strategy/date-range result.

   Rationale: Backtests may be rerun for the same strategy, configuration version, parameters, and date range after code or data changes. Preserving multiple runs keeps research history and failure diagnostics available.

   Alternative considered: enforce one row per strategy/configuration/date range. That simplifies lookup, but loses rerun history and makes experiments harder to compare.

2. Store backtest parameters as serialized JSON text.

   Rationale: Backtest parameter shape is likely to change while the engine is still being designed. A text snapshot preserves the exact input without forcing premature columns for universe, rebalance cadence, fees, slippage, or other strategy-specific options.

   Alternative considered: structured parameter columns. Those would improve filtering on known parameters, but require decisions that are not yet stable in Phase 1.

3. Store core metrics as nullable numeric columns on `BacktestRun`.

   Rationale: Total return, annualized return, maximum drawdown, Sharpe ratio, and volatility are expected comparison fields for backtest result lists. Keeping them as columns supports straightforward filtering and ordering, while nullable values allow running or failed backtests.

   Alternative considered: store all metrics as JSON text. That is flexible, but weak for comparing runs and filtering by common metrics.

4. Store equity curve data in `BacktestEquityPoint`.

   Rationale: Equity curve points need date-based lookup, uniqueness per run/date, and direct ORM navigation from a run. A child table keeps curve data queryable and avoids loading large JSON blobs when only run metadata is needed.

   Alternative considered: store the curve as JSON text on `BacktestRun`. That is smaller initially, but makes date-range queries and duplicate-point protection harder.

5. Use string value sets in the model, not database enums.

   Rationale: Existing lifecycle models use string fields with `ClassVar` allowed values. Keeping this pattern avoids enum migration complexity before backtest services exist.

   Alternative considered: database enum or check constraints. This gives stronger enforcement, but adds portability and migration friction in the current SQLite-oriented foundation.

## Risks / Trade-offs

- JSON text parameters are not easy to query by individual parameter values -> Add structured columns later only for parameters that become stable query needs.
- Nullable metrics permit incomplete successful rows -> Let future backtest services validate lifecycle and metric consistency.
- Equity curves can become large -> Keep run metadata and curve points split, and index curve lookup by run and trade date.
- Multiple reruns require explicit latest-run selection later -> Add indexes for strategy/configuration and status/start time so query services can choose ordering.

## Migration Plan

- Create an Alembic migration after the existing strategy signal migration.
- Add `backtest_run` with lifecycle fields, parameter snapshot, core metrics, timestamps, and lookup indexes.
- Add `backtest_equity_point` with a foreign key to `backtest_run`, a unique constraint on `(backtest_run_id, trade_date)`, and a lookup index.
- Rollback drops the equity point indexes/table before dropping the run indexes/table.

## Open Questions

- None for this proposal.

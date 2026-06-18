## Context

`BacktestRun` already models one historical backtest execution. The current daily curve data is stored in `BacktestEquityPoint`, which only records `trade_date` and `net_value`.

Backtest review needs a daily portfolio snapshot, not just a scalar net value. The model should make the richer shape explicit while keeping Phase 1 simple and testable.

## Goals / Non-Goals

**Goals:**
- Replace `BacktestEquityPoint` with `BacktestEquityCurve`.
- Store one curve row per `BacktestRun` and trading date.
- Persist daily net value, cash, market value, total assets, and serialized positions.
- Keep SQLAlchemy relationships explicit from `BacktestRun` to curve rows and from each curve row to its parent run.
- Use a forward Alembic migration instead of editing the existing `0005` migration.

**Non-Goals:**
- Do not implement backtest engine persistence logic.
- Do not introduce a normalized daily holdings table.
- Do not add result analysis APIs or query services.
- Do not keep `BacktestEquityPoint` as a compatibility alias.

## Decisions

1. Use `BacktestEquityCurve` as the only daily curve model.

   Rationale: The old `BacktestEquityPoint` name describes a single net value point, while the new model stores a portfolio snapshot. Keeping both names would create duplicate concepts early in the backend.

   Alternative considered: extend `BacktestEquityPoint` in place. That would be smaller but would leave the public model name inconsistent with the richer data.

2. Store positions as `positions_json` text.

   Rationale: Phase 1 should preserve the daily holdings snapshot without prematurely designing a separate holdings table. A serialized snapshot matches the existing `parameters_json` pattern on `BacktestRun`.

   Alternative considered: create a `BacktestEquityCurvePosition` child table. That may be useful later, but it adds schema and relationship complexity before query requirements are known.

3. Add `cash`, `market_value`, and `total_assets` as numeric columns.

   Rationale: These are core portfolio summary values that should be queryable and testable without parsing JSON. Use the existing `Numeric(18, 6)` precision pattern from backtest metrics and prices.

   Alternative considered: store all portfolio data in JSON. That is flexible, but it makes common portfolio summary queries harder and less explicit.

4. Use `BacktestRun.equity_curve` and `BacktestEquityCurve.backtest_run` relationships.

   Rationale: `equity_curve` names the collection as the run's time series, while the child relationship mirrors existing parent-link style.

   Alternative considered: keep `equity_points` as the run relationship. That would preserve old naming but conflicts with the removal of `BacktestEquityPoint`.

## Risks / Trade-offs

- Dropping `backtest_equity_point` removes existing rows during migration. → Accept for this Phase 1 model change; the project is still defining the backend foundation, and no compatibility alias is desired.
- `positions_json` is not relationally queryable. → Accept until concrete holdings-level query requirements exist.
- Renaming the model is a breaking import change. → Update exports, Alembic imports, and tests in the same implementation change.

## Migration Plan

- Add a new Alembic revision after `20260618_0005`.
- In upgrade, create `backtest_equity_curve` with the new fields, foreign key, unique constraint, and lookup index; then drop `backtest_equity_point`.
- In downgrade, recreate `backtest_equity_point` with its previous structure and constraints; then drop `backtest_equity_curve`.
- Update ORM metadata imports so Alembic discovers `backtest_equity_curve` and no longer imports `BacktestEquityPoint`.

## Open Questions

None.

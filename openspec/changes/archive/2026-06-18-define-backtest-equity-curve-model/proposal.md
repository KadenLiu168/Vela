## Why

Backtest result analysis needs more than one net value point per trading day. Each backtest trading day should persist the curve value together with the key portfolio snapshot data needed to inspect how the run evolved.

The existing `BacktestEquityPoint` model only captures `trade_date` and `net_value`, so it is too narrow for daily portfolio-level backtest review.

## What Changes

- **BREAKING** Replace `BacktestEquityPoint` with `BacktestEquityCurve`; do not keep the old class, export, table, or relationship as a compatibility alias.
- Add daily portfolio snapshot fields to the equity curve model: cash, market value, total assets, and serialized positions.
- Keep a required foreign key from each equity curve row to `BacktestRun`.
- Keep duplicate protection for one curve row per backtest run and trading date.
- Add a forward Alembic migration that creates `backtest_equity_curve` and removes `backtest_equity_point`.
- Leave backtest engine write logic, position detail tables, and result analysis APIs out of this change.

## Capabilities

### New Capabilities

### Modified Capabilities
- `backtest-run-model`: Replace the narrow `BacktestEquityPoint` requirement with a wider `BacktestEquityCurve` requirement for daily net value and portfolio snapshot data.

## Impact

- Core SQLAlchemy models and exports under `packages/core/src/vela_core/models`.
- Alembic migration metadata and a new forward migration.
- Backtest model tests that currently reference `BacktestEquityPoint`.
- OpenSpec `backtest-run-model` requirements for equity curve persistence.

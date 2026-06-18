## 1. Tests

- [x] 1.1 Update backtest model tests to import and inspect `BacktestEquityCurve` instead of `BacktestEquityPoint`.
- [x] 1.2 Add tests that `BacktestEquityCurve` exposes `id`, `backtest_run_id`, `trade_date`, `net_value`, `cash`, `market_value`, `total_assets`, `positions_json`, and `created_at`.
- [x] 1.3 Add tests for the `BacktestEquityCurve.backtest_run` foreign key and `BacktestRun.equity_curve` relationship.
- [x] 1.4 Add tests that duplicate `backtest_run_id` and `trade_date` curve rows are rejected, while the same `trade_date` is allowed across different runs.
- [x] 1.5 Add tests that Alembic metadata includes `backtest_equity_curve` and no longer includes `backtest_equity_point`.

## 2. ORM Model

- [x] 2.1 Replace the `BacktestEquityPoint` class with `BacktestEquityCurve` in the backtest model module.
- [x] 2.2 Add `cash`, `market_value`, `total_assets`, and `positions_json` columns to `BacktestEquityCurve`.
- [x] 2.3 Rename relationship wiring to `BacktestRun.equity_curve` and `BacktestEquityCurve.backtest_run`.
- [x] 2.4 Update model exports so `BacktestEquityCurve` is public and `BacktestEquityPoint` is not exported.

## 3. Migration

- [x] 3.1 Update Alembic model imports to include `BacktestEquityCurve` and remove `BacktestEquityPoint`.
- [x] 3.2 Add a new Alembic revision after `20260618_0005` that creates `backtest_equity_curve` with the required columns, foreign key, unique constraint, and index.
- [x] 3.3 In the new migration upgrade, drop the old `backtest_equity_point` table after creating `backtest_equity_curve`.
- [x] 3.4 In the new migration downgrade, recreate `backtest_equity_point` with its previous schema and drop `backtest_equity_curve`.

## 4. Verification

- [x] 4.1 Run the focused backtest model test file.
- [x] 4.2 Run the project test suite or the nearest available core package test command.
- [x] 4.3 Run OpenSpec validation/status checks for `define-backtest-equity-curve-model`.

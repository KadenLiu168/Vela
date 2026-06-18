## 1. Specification Validation

- [x] 1.1 Run `openspec status --change "define-backtest-run-model"` and confirm the change is apply-ready.

## 2. Model Tests

- [x] 2.1 Add focused tests for `BacktestRun` required columns, nullable completion fields, status values, and serialized parameter storage.
- [x] 2.2 Add tests confirming multiple `BacktestRun` rows with the same strategy name, configuration version, and date range are allowed.
- [x] 2.3 Add focused tests for `BacktestEquityPoint` required columns, foreign key, and ORM relationships.
- [x] 2.4 Add tests confirming duplicate `backtest_run_id` and `trade_date` equity point rows are rejected.
- [x] 2.5 Add tests confirming the same trading date can appear in different backtest runs.
- [x] 2.6 Add tests for backtest run and equity point lookup indexes.

## 3. ORM Implementation

- [x] 3.1 Add `BacktestRun` with strategy name, configuration version, date range, serialized parameters, lifecycle fields, core metrics, and audit timestamps.
- [x] 3.2 Add `BacktestEquityPoint` with backtest run foreign key, trading date, net value, and creation timestamp.
- [x] 3.3 Add `BacktestRun.STATUSES` with the supported values from the spec.
- [x] 3.4 Add the unique constraint on `BacktestEquityPoint.backtest_run_id` and `BacktestEquityPoint.trade_date`.
- [x] 3.5 Add indexes for strategy/configuration lookup, status/start-time lookup, requested date range lookup, and equity curve lookup by run/date.
- [x] 3.6 Add typed SQLAlchemy `relationship()` attributes for `BacktestRun.equity_points` and `BacktestEquityPoint.backtest_run`.
- [x] 3.7 Expose both models through `vela_core.models` so `Base.metadata` includes both tables.

## 4. Migration

- [x] 4.1 Update Alembic model imports so migration autogeneration can discover `BacktestRun` and `BacktestEquityPoint`.
- [x] 4.2 Add an Alembic migration that creates the backtest tables, foreign key, unique constraint, and indexes.

## 5. Verification

- [x] 5.1 Run `uv run pytest packages/core/tests`.
- [x] 5.2 Run `openspec status --change "define-backtest-run-model"` and confirm the change remains apply-ready.

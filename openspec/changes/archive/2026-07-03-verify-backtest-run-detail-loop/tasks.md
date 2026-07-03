## 1. Closed-Loop Test

- [x] 1.1 Add a focused API integration test that posts run backtest and then reads backtest detail from the same SQLite database.
- [x] 1.2 Assert `BacktestRun` and ordered `BacktestEquityCurve` persistence after execution.
- [x] 1.3 Assert the detail response identifies the generated run and includes metrics and equity curve rows.

## 2. Validation

- [x] 2.1 Run focused pytest validation for backtest run, detail, and Dashboard API tests.
- [x] 2.2 Run repository validation commands required for this change.
- [x] 2.3 Run OpenSpec validation for the change.

## 3. Completion

- [x] 3.1 Review the COP-126 diff for scope, correctness, and spec alignment.
- [x] 3.2 Archive the OpenSpec change after validation passes.

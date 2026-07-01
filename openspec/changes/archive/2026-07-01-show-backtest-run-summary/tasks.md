## 1. Dashboard Implementation

- [x] 1.1 Store the successful backtest run API response in Dashboard operation state.
- [x] 1.2 Render a backtest run summary with run id, status, trading day count, signal count, and core metrics.
- [x] 1.3 Add a Backtest Detail entry point that links to `/backtests/<run id>`.
- [x] 1.4 Ensure failed backtest submissions clear any previous success summary and keep the operation-level error path.

## 2. Tests

- [x] 2.1 Update Dashboard tests to assert the successful backtest run summary and detail link.
- [x] 2.2 Add or update Dashboard tests to assert failed backtest submissions do not show a stale success summary.

## 3. Validation

- [x] 3.1 Run relevant frontend tests.
- [x] 3.2 Run frontend lint/typecheck/build commands if available.
- [x] 3.3 Run OpenSpec validation for `show-backtest-run-summary`.

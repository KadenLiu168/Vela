## 1. API Client Tests

- [x] 1.1 Add frontend API client test coverage for `runBacktest(startDate, endDate)` calling the real run-backtest route shape.
- [x] 1.2 Add frontend API integration validation for `runBacktest` behind `VITE_API_BASE_URL`.

## 2. Dashboard Form Tests

- [x] 2.1 Add Dashboard tests for visible start/end date inputs and valid submit behavior.
- [x] 2.2 Add Dashboard tests for invalid date format and `startDate > endDate` without API submission.
- [x] 2.3 Add Dashboard tests for pending duplicate-submit prevention and minimal success feedback.

## 3. Implementation

- [x] 3.1 Add typed `BacktestRunResponse` and `runBacktest` shared client helper.
- [x] 3.2 Add Dashboard local form state, validation, submit handling, and operation error coverage for backtest runs.
- [x] 3.3 Style the backtest form using existing Dashboard operation visual patterns.

## 4. Validation

- [x] 4.1 Run focused frontend tests and fix regressions.
- [x] 4.2 Run package validation commands available in `apps/web/package.json`.
- [x] 4.3 Run backend run-backtest API validation that proves SQLite persistence remains covered.
- [x] 4.4 Run OpenSpec validation for the change.

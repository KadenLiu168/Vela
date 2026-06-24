## 1. Core Report Export

- [x] 1.1 Add a backtest report not-found error type.
- [x] 1.2 Implement `export_backtest_report(session, run_id=...)` using `get_backtest_result`.
- [x] 1.3 Format run metadata, metrics, parameters, and curve summary rows.
- [x] 1.4 Export the report error and function from `vela_core`.

## 2. CLI Command

- [x] 2.1 Add `export-backtest-report` parser arguments for database URL, run id, and optional output path.
- [x] 2.2 Add CLI wrapper and error handling for missing backtest runs.
- [x] 2.3 Support stdout output and file output with confirmation.

## 3. Tests

- [x] 3.1 Add core report tests for metrics, curve summary, empty curve, and missing run.
- [x] 3.2 Add CLI tests for argument forwarding, default database, file output, and missing run failure.

## 4. Verification

- [x] 4.1 Run targeted core and CLI report tests.
- [x] 4.2 Run full tests, lint, type check, and OpenSpec validation.

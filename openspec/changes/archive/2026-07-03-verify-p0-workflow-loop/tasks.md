## 1. Full Workflow Test

- [x] 1.1 Add a focused API integration test that reads Dashboard, fetches market data, generates a signal, runs a backtest, and reads backtest detail from the same SQLite database.
- [x] 1.2 Assert refreshed Dashboard state includes persisted market data, latest signal, recent backtest, and fetch log state.
- [x] 1.3 Assert latest signal and backtest detail follow-up reads restore the generated persisted results.
- [x] 1.4 Record backend/API gaps or field mismatches found during validation.

## 2. Dashboard Detail Entry Points

- [x] 2.1 Add a Signal Detail entry point to populated Dashboard latest signal summaries.
- [x] 2.2 Add a Backtest Detail entry point to populated Dashboard recent backtest summaries.
- [x] 2.3 Cover persisted Dashboard detail entry points in frontend tests.

## 3. Validation

- [x] 3.1 Run focused pytest validation for the full P0 workflow and related API tests.
- [x] 3.2 Run repository validation commands required for this change.
- [x] 3.3 Run OpenSpec validation for the change.

## 4. Completion

- [x] 4.1 Review the COP-127 diff for scope, correctness, and spec alignment.
- [x] 4.2 Archive the OpenSpec change after validation passes.

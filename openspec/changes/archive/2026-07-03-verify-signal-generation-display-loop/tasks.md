## 1. Closed-Loop Test

- [x] 1.1 Add a focused API integration test that posts signal generation and then reads latest signal and Dashboard from the same SQLite database.
- [x] 1.2 Assert `StrategySignal` and `StrategySignalPosition` persistence after generation.
- [x] 1.3 Assert latest signal and Dashboard responses identify the same generated signal and position count.

## 2. Validation

- [x] 2.1 Run focused pytest validation for signal generation, latest signal, and Dashboard API tests.
- [x] 2.2 Run repository validation commands required for this change.
- [x] 2.3 Run OpenSpec validation for the change.

## 3. Completion

- [x] 3.1 Review the COP-125 diff for scope, correctness, and spec alignment.
- [x] 3.2 Archive the OpenSpec change after validation passes.

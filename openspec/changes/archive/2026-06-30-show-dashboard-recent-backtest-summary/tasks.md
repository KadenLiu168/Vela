## 1. Frontend recent backtest rendering

- [x] 1.1 Add focused Dashboard rendering coverage for populated recent backtest date range, status, and core metric values.
- [x] 1.2 Add focused Dashboard rendering coverage for the empty recent backtest state with a run-backtest entry point.
- [x] 1.3 Update the recent backtest panel implementation only as needed to satisfy the empty-state entry point requirement.

## 2. Real API validation

- [x] 2.1 Tighten dashboard API SQLite integration assertions so persisted `BacktestRun` date range, status, and metric values are explicitly validated.
- [x] 2.2 Confirm no new API route, schema migration, or mocked-only validation path is introduced.

## 3. Validation and review

- [x] 3.1 Run focused backend/API/frontend tests for the recent backtest summary behavior.
- [x] 3.2 Run project lint/typecheck/OpenSpec validation commands available for this scope.
- [x] 3.3 Review the change for COP-91-only scope and update OpenSpec artifacts if implementation behavior diverges.

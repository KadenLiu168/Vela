## 1. Dashboard Implementation

- [x] 1.1 Refresh Dashboard aggregate state after a successful Dashboard backtest run.
- [x] 1.2 Keep failed Dashboard backtest submissions on the existing operation-level error path without issuing an extra Dashboard refresh.
- [x] 1.3 Preserve the immediate Operations panel run response summary from COP-108.

## 2. Tests

- [x] 2.1 Add or update Dashboard tests to assert the Recent backtest panel refreshes from `GET /api/dashboard` after a successful run.
- [x] 2.2 Add or update Dashboard tests to assert browser refresh restores the persisted recent backtest summary from the backend Dashboard response.
- [x] 2.3 Add or update Dashboard tests to assert failed backtest submissions do not issue an additional Dashboard refresh or render a stale success summary.

## 3. Validation

- [x] 3.1 Run focused frontend tests for Dashboard and API client behavior.
- [x] 3.2 Run frontend lint and build/typecheck validation.
- [x] 3.3 Run OpenSpec validation for `refresh-dashboard-recent-backtest`.

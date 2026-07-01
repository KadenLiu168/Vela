## 1. Tests

- [x] 1.1 Add API integration tests for existing run detail, equity curve ordering, and missing run not found.
- [x] 1.2 Run the focused API test and confirm the new detail tests fail before implementation.

## 2. API Implementation

- [x] 2.1 Add the `GET /api/backtests/{run_id}` route using the existing persisted result query helper.
- [x] 2.2 Add response shaping for run metadata, metrics, and equity curve points.
- [x] 2.3 Return a stable 404 not-found error for missing run ids.

## 3. Validation

- [x] 3.1 Run focused API tests for backtest endpoints.
- [x] 3.2 Run relevant or full Python tests, ruff check, ruff format check, and OpenSpec validation.
- [x] 3.3 Archive the OpenSpec change after tasks and specs are complete.

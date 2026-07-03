## Why

COP-126 requires validation that Dashboard-submitted backtests reach the backend workflow, persist `BacktestRun` and `BacktestEquityCurve`, and are then readable by the Backtest Detail API that powers the frontend detail page. Existing tests cover run persistence, detail reads, and frontend rendering separately, but they do not prove the run-to-detail closed loop in one flow.

## What Changes

- Add an API integration test that posts to the run backtest endpoint and then reads the generated run through the backtest detail endpoint from the same temporary SQLite database.
- Verify the backend persists the generated `BacktestRun` and ordered `BacktestEquityCurve` rows.
- Verify the detail API returns metrics and equity curve data for the same generated run id.
- Keep frontend behavior unchanged because existing tests already validate Dashboard run submission, result link, metric cards, and equity curve rendering from API-shaped responses.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `http-api-service`: Require a closed-loop validation that backtest run persistence is visible through the backtest detail API.
- `test-suite-validation`: Require pytest coverage for the COP-126 backtest run to detail display data-source loop.

## Impact

- Affected tests: `apps/api/tests/test_backtest_run.py`
- Affected OpenSpec files: `http-api-service`, `test-suite-validation`
- No API contract changes.
- No new dependencies.

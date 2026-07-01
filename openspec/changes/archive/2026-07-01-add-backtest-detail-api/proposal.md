## Why

Backtest runs can already be executed and listed, but clients cannot retrieve the persisted details for one run. A detail endpoint is needed so downstream UI and analysis workflows can inspect a run's metadata, metrics, and equity curve from the durable database records.

## What Changes

- Add a read-only `GET /api/backtests/{run_id}` endpoint.
- Return structured JSON containing the selected `BacktestRun` metadata, metrics, and related `BacktestEquityCurve` rows.
- Return equity curve points ordered by trading date ascending.
- Return a stable not-found error when the run id does not exist.
- Validate the endpoint with a temporary SQLite database containing real persisted backtest rows.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `http-api-service`: add a backtest detail endpoint requirement and integration validation.

## Impact

- `apps/api/src/vela_api/main.py`: add the read-only route and response shaping.
- `apps/api/tests/test_backtest_run.py`: add integration tests using persisted `BacktestRun` and `BacktestEquityCurve` rows.
- `openspec/specs/http-api-service/spec.md`: updated through this change's delta spec when archived.

## Why

COP-104 needs a frontend-callable way to run a historical backtest without shelling out to the CLI. The core `run_backtest` capability already persists `BacktestRun` and `BacktestEquityCurve`, but the HTTP API does not expose it.

## What Changes

- Add `POST /api/backtests/run` accepting `startDate` and `endDate` query parameters.
- Have the endpoint load the default strategy config, call existing core `run_backtest`, and return the persisted run summary.
- Add integration validation using the local FastAPI app, a temporary SQLite database, and the real core backtest workflow.
- Do not add backtest listing, detail retrieval, frontend behavior, or new persistence models.

## Capabilities

### New Capabilities

### Modified Capabilities
- `http-api-service`: Add a frontend-callable run backtest command endpoint and integration validation.

## Impact

- API: `apps/api/src/vela_api/main.py`
- Tests: `apps/api/tests/`
- Specs: `openspec/specs/http-api-service/spec.md`

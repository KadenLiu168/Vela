## Why

COP-86 needs a local Dashboard API that can load the first-screen workflow state in one request. The current API exposes health and config only, so the frontend cannot inspect stored market data, latest signals, or recent backtests without future endpoint sprawl.

## What Changes

- Add a dashboard aggregate read model in `vela_core` that summarizes strategy configuration, local market price coverage, the latest persisted strategy signal, and the most recent persisted backtest.
- Expose `GET /api/dashboard` from the FastAPI app using the existing request-scoped SQLite session dependency.
- Validate the endpoint with real SQLite tables, SQLAlchemy ORM models, and the local API test client.
- Keep the endpoint read-only and do not add signal generation, backtest execution, or frontend rendering behavior.

## Capabilities

### New Capabilities
- `dashboard-aggregation`: Dashboard first-screen aggregate read behavior across strategy config, market price coverage, latest signal, and recent backtest data.

### Modified Capabilities
- `http-api-service`: Add a read-only dashboard aggregate endpoint backed by the core dashboard aggregation service.

## Impact

- Affected code: `packages/core/src/vela_core`, `apps/api/src/vela_api`.
- Affected tests: focused core dashboard aggregation tests and API integration tests with real SQLite data.
- Affected APIs: new `GET /api/dashboard` response for the local web Dashboard.
- Dependencies: none.

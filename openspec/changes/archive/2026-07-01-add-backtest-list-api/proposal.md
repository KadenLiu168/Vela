## Why

Dashboard and backtest result entry points need a lightweight way to discover recent persisted backtest runs. The API can already execute a backtest, but clients cannot list historical `BacktestRun` rows without using the dashboard aggregate's single-run summary.

## What Changes

- Add a read-only `GET /api/backtests` endpoint that returns recent persisted backtest runs.
- Support a simple `limit` query parameter for bounding the number of returned runs.
- Include run id, date range, status, start/end timestamps, and core metric summary fields in each list item.
- Query real `BacktestRun` rows through the request-scoped database session.
- Do not add run detail, equity curve, advanced filters, frontend UI, or dashboard backfill behavior.

## Capabilities

### New Capabilities

### Modified Capabilities
- `http-api-service`: Add a read-only recent backtest run list endpoint and integration validation.

## Impact

- Affected API: `GET /api/backtests`.
- Affected code: FastAPI route wiring in `apps/api`, using existing `BacktestRun` ORM rows.
- Affected tests: API integration tests against temporary SQLite databases.
- Dependencies: no new runtime dependencies.

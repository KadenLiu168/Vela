## Why

COP-110 needs the Backtest Detail route to become a useful persisted-result view instead of a placeholder. The backend already exposes a real backtest detail API, so the frontend should load one run by id and show the core run metadata users need to inspect a completed or failed run.

## What Changes

- Replace the Backtest Detail placeholder with a page that loads `GET /api/backtests/{run_id}` through the shared frontend API client.
- Show run metadata, date range, status, timestamps, error message, metrics, and a readable parameter summary from the API response.
- Render stable loading, API failure, and not-found states for missing or unavailable runs.
- Add frontend API client types and tests for the backtest detail endpoint.
- Do not add equity curve charts, holdings tables, backend routes, database changes, or new dependencies.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Backtest Detail route loads and renders persisted backtest run detail from the real API.

## Impact

- Affects `apps/web/src/api/client.ts`, `apps/web/src/pages/BacktestDetailPage.tsx`, and related frontend tests.
- Updates the `web-frontend-app` OpenSpec capability.
- Reuses the existing `GET /api/backtests/{run_id}` backend contract without changing backend code.

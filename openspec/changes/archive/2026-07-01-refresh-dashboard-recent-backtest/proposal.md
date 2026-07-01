## Why

After a Dashboard backtest run succeeds, the Operations panel shows the immediate API response but the Recent backtest panel can still show stale dashboard data until the browser reloads. Users need the Dashboard summary to refresh from the backend persisted result so the first-screen state matches the backtest detail workflow and survives page refresh.

## What Changes

- Refresh Dashboard aggregate state after `POST /api/backtests/run` succeeds.
- Ensure the Recent backtest panel renders the same persisted run returned by the backend Dashboard API.
- Preserve the existing Operations panel run result summary and failure behavior from COP-108.
- Do not change the run backtest API request or response contract.
- Do not add backend models, migrations, or new API endpoints.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Dashboard backtest submission must refresh and render the backend-persisted recent backtest summary after a successful run.

## Impact

- Affects `apps/web/src/pages/DashboardPage.tsx` and related frontend tests.
- Updates the `web-frontend-app` OpenSpec capability.
- No backend API, database, dependency, or routing contract changes are expected.

## Why

The frontend Dashboard route is still a placeholder, so local research users cannot review workflow state or reach the next core actions from the first screen. COP-86 added `GET /api/dashboard`; COP-87 should render that aggregate in a clear local-tool layout.

## What Changes

- Replace the Dashboard placeholder with a first-screen layout for market data status, strategy summary, latest signal, recent backtest, and core operations.
- Add typed frontend API support for `GET /api/dashboard` using the existing shared API client.
- Render loading, API error, and empty-data states without introducing new frontend dependencies.
- Add focused frontend tests for dashboard API loading and rendered sections.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-frontend-app`: The default Dashboard route must render the workflow dashboard layout using the dashboard aggregate API contract.

## Impact

- Affected code: `apps/web/src/api/client.ts`, `apps/web/src/pages/DashboardPage.tsx`, `apps/web/src/styles.css`, and frontend tests.
- Affected APIs: consumes existing `GET /api/dashboard`; no backend API changes.
- Dependencies: no new runtime or development dependencies expected.

## Why

The Dashboard can already trigger incremental market data fetching, but it does not expose the existing full fetch API for first-time initialization or local data repair. COP-96 needs a lower-priority frontend entry point for that heavier operation while keeping incremental fetch as the normal action.

## What Changes

- Add a shared frontend API helper for `POST /api/market-data/fetch?mode=full`.
- Add a secondary Dashboard operation action that triggers full market data fetching after the incremental action.
- Reuse the existing Dashboard market data fetch summary for full fetch results.
- Add frontend validation that exercises the full fetch helper against the real local API response contract backed by SQLite.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add a lower-priority Dashboard full market data fetch entry point using the existing fetch summary and local API integration validation.

## Impact

- Affected code: `apps/web/src/api/client.ts`, `apps/web/src/pages/DashboardPage.tsx`.
- Affected tests: frontend API client tests, Dashboard tests, and frontend local API integration tests.
- API surface: no backend API change; this reuses `POST /api/market-data/fetch?mode=full`.
- Dependencies: no new dependencies expected.

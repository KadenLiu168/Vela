## Why

Dashboard currently shows market data status but the market data fetch entry point is disabled. COP-94 needs the first frontend operation that lets a user trigger the existing incremental market data fetch workflow and see refreshed Dashboard state afterward.

## What Changes

- Enable the Dashboard market data fetch action as an incremental fetch operation.
- Add shared frontend API client support for `POST /api/market-data/fetch?mode=incremental`.
- Show an in-progress state while the operation is running and prevent duplicate fetch submissions.
- Refresh Dashboard aggregate data after a successful incremental fetch.
- Validate the frontend behavior with component/client tests and a real local API + SQLite validation path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Add Dashboard incremental market data fetch operation behavior and validation expectations.

## Impact

- Affected frontend code: `apps/web/src/api/client.ts`, `apps/web/src/pages/DashboardPage.tsx`, and related frontend tests.
- Uses the existing COP-93 backend endpoint `POST /api/market-data/fetch?mode=incremental`.
- No backend API contract changes and no new dependencies are expected.

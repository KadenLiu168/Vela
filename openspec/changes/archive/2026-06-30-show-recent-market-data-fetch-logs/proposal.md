## Why

Dashboard users can run market data fetches, but they cannot see recent persisted fetch history after the immediate operation summary disappears. COP-97 needs a small first-phase view into recent `DataFetchLog` rows so users can understand the latest fetch timing, mode, outcome, row counts, and failure summaries.

## What Changes

- Add recent market data fetch log summaries to the Dashboard aggregate read model.
- Return those summaries from the existing `GET /api/dashboard` response.
- Render a compact recent fetch history section on the Dashboard.
- Keep the feature intentionally narrow: no log center, filtering, pagination, search, or new fetch workflow behavior.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dashboard-aggregation`: Include recent market data fetch log summaries from real `DataFetchLog` rows.
- `http-api-service`: Return recent fetch log summaries through the dashboard endpoint contract.
- `web-frontend-app`: Render recent fetch log history from the dashboard aggregate response.

## Impact

- Affected core code: `packages/core/src/vela_core/dashboard_aggregation.py`
- Affected API code: `apps/api/src/vela_api/main.py` via existing dashboard delegation and API tests
- Affected frontend code: `apps/web/src/api/client.ts`, `apps/web/src/pages/DashboardPage.tsx`
- Affected tests: dashboard aggregation, dashboard API, frontend API client, and Dashboard UI tests
- No database schema, dependency, or route addition is expected.

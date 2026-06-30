## Context

COP-93 added `POST /api/market-data/fetch?mode=incremental|full` and validated that the endpoint persists `DataFetchLog` and `MarketPrice` rows through a real SQLite-backed request. The Dashboard already loads aggregate state through the shared frontend API client and renders disabled market-data operation entry points.

## Goals / Non-Goals

**Goals:**

- Let a Dashboard user trigger the existing incremental market data fetch API.
- Show a clear in-progress state and avoid duplicate submissions while the fetch is running.
- Refresh Dashboard aggregate data after the fetch succeeds.
- Validate both frontend interaction and the real local API + SQLite path.

**Non-Goals:**

- Add full fetch controls or mode selection.
- Change the COP-93 API contract or backend fetch workflow.
- Add global state management, background polling, or production deployment behavior.

## Decisions

- Use the existing shared API client for the fetch operation.
  - Rationale: Dashboard code already depends on `apps/web/src/api/client.ts` for aggregate data; keeping endpoint calls there preserves the existing pattern.
  - Alternative considered: call `fetch` directly in `DashboardPage`; rejected because it bypasses the shared client requirement already established for Dashboard.
- Keep fetch state local to `DashboardPage`.
  - Rationale: COP-94 only needs a single Dashboard operation, so component state is enough.
  - Alternative considered: introduce a reusable operation state abstraction; rejected as unnecessary for one operation.
- Trigger only `mode=incremental`.
  - Rationale: COP-94 asks for incremental fetch specifically and COP-93 already provides the backend mode parameter.
  - Alternative considered: expose both incremental and full modes; rejected as outside this issue.

## Risks / Trade-offs

- Fetch failures may leave Dashboard data unchanged -> show a concise operation failure state and keep the action available for retry.
- The real local API integration test depends on a running API service -> keep it opt-in through the existing `VITE_API_BASE_URL` integration script.

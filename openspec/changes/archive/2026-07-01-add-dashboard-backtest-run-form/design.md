## Context

The Dashboard already has an Operations panel for local workflow commands and a disabled `Run backtest` placeholder. The backend run-backtest API already exists at `POST /api/backtests/run?startDate=...&endDate=...`, and backend API tests validate that it runs the core workflow and persists `BacktestRun` plus `BacktestEquityCurve` rows in SQLite.

## Goals / Non-Goals

**Goals:**

- Add a minimal, fully interactive Dashboard date-range form for running a backtest.
- Reuse the shared frontend API client and existing Dashboard operation styling.
- Validate date format and date ordering before any network request.
- Show scoped operation feedback after submit.

**Non-Goals:**

- Do not add a Backtest Detail page entry point.
- Do not refresh or backfill the Dashboard recent-backtest panel after submit.
- Do not build a rich post-run result summary beyond minimal operation status.
- Do not change backend API behavior.

## Decisions

- Add a `runBacktest(startDate, endDate)` helper in `apps/web/src/api/client.ts`.
  - Rationale: Dashboard page code already calls API through endpoint helpers instead of direct `fetch`.
  - Alternative considered: call `apiRequest` directly from `DashboardPage`; rejected because it breaks the shared-client pattern.

- Keep backtest form state local to `DashboardPage`.
  - Rationale: The form is currently Dashboard-only and does not need cross-route state.
  - Alternative considered: extract a reusable component immediately; rejected because this is the only consumer.

- Use strict `YYYY-MM-DD` validation before submit.
  - Rationale: The API expects ISO date query parameters, and client-side feedback should catch bad input before the backend 422/400 path.
  - Alternative considered: rely on `<input type="date">` alone; rejected because tests and browser behavior should not be the only validator.

- Render only a scoped submission-success message after the API request succeeds.
  - Rationale: COP-108 owns richer submitted-run result summaries and COP-109 owns recent-backtest refresh/backfill.
  - Alternative considered: reload Dashboard after success; rejected because it would overlap COP-109.

## Risks / Trade-offs

- Browser date input support can vary by environment -> keep explicit string validation in submit handling.
- A successful run will not update the recent-backtest panel immediately -> this is intentional to preserve COP-109 scope.
- Backend failures can contain useful detail text, but current `ApiClientError` operation errors expose only kind/status in Dashboard copy -> keep the existing concise error pattern unless later UX work expands it.

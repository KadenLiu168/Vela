## Context

`apps/web` is a Vite React TypeScript frontend with a minimal route shell and placeholder Dashboard. COP-86 added the backend `GET /api/dashboard` aggregate with strategy, market data, latest signal, and recent backtest fields. COP-87 connects that contract to the default route and makes the first screen useful for local research workflow review.

## Goals / Non-Goals

**Goals:**
- Consume `GET /api/dashboard` through the existing shared API client pattern.
- Render a dense but readable local research dashboard with market status, strategy summary, latest signal, recent backtest, and operation entry points.
- Cover loading, API failure, and empty latest signal/backtest states.
- Add focused frontend tests without requiring a running backend service.

**Non-Goals:**
- Do not change the backend dashboard API contract.
- Do not implement signal generation, market data fetching, or backtest run actions from the UI.
- Do not add charting, widget configuration, authentication, or new frontend dependencies.
- Do not implement COP-88 behavior.

## Decisions

1. Add a typed `getDashboard()` helper in `apps/web/src/api/client.ts`.
   - Rationale: Existing frontend code centralizes API calls in the shared client. Keeping Dashboard on that path preserves normalized network and HTTP error behavior.
   - Alternative considered: call `fetch` directly in `DashboardPage`. Rejected because it bypasses the existing client contract.

2. Keep Dashboard rendering in `DashboardPage.tsx` with small local formatting helpers.
   - Rationale: The page is still narrow and single-use. Extracting components now would add structure before reuse exists.
   - Alternative considered: introduce a dashboard component folder. Rejected as unnecessary for the COP-87 surface.

3. Render operation entries as visible local workflow controls without wiring side effects.
   - Rationale: COP-87 asks for core operation entry points, while action execution belongs to later issues. Buttons can communicate the intended operations without pretending they are implemented.
   - Alternative considered: hide actions until endpoints exist. Rejected because the acceptance criteria explicitly includes an operation area.

## Risks / Trade-offs

- API service may be unavailable during local frontend work -> show a concise error state while preserving the Dashboard shell.
- Empty databases return `null` latest signal/backtest -> render explicit empty-state copy rather than treating it as an error.
- Numeric API values are strings for decimals -> display them conservatively as received, with lightweight percent formatting only when parseable.

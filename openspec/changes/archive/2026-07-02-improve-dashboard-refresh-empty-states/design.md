## Context

The Dashboard already loads `GET /api/dashboard`, exposes long-running local operations, and refreshes relevant data after market data fetches, signal generation, and backtest runs. First-run guidance, loading feedback, and operation error summaries are already present.

The remaining COP-119 scope is a frontend-only refinement: add a manual refresh path, keep operation completion separate from refresh failure, and make empty-state copy point to the exact next Dashboard action.

## Goals / Non-Goals

**Goals:**

- Provide a manual Dashboard refresh action using the existing `getDashboard()` helper.
- Reuse the same Dashboard refresh path for initial load, manual refresh, and post-operation refreshes.
- Keep successful operation summaries visible even if the follow-up Dashboard refresh fails.
- Align empty-state copy with the Operations panel controls users already have.

**Non-Goals:**

- Add or change backend APIs.
- Add polling, realtime updates, or background refresh intervals.
- Redesign the Dashboard layout.
- Change Signal Detail or Backtest Detail behavior.

## Decisions

1. Use the existing Dashboard aggregate endpoint for manual refresh.
   - Rationale: `GET /api/dashboard` is already the source of truth for the page's status panels.
   - Alternative considered: add endpoint-specific refresh controls per panel. Rejected because COP-119 asks for Dashboard status refresh, and per-panel refresh would expand the surface.

2. Track Dashboard refresh failure as Dashboard state instead of operation failure when the operation request already succeeded.
   - Rationale: a successful fetch, signal generation, or backtest run should keep its operation summary visible; a later refresh failure is a page state problem.
   - Alternative considered: keep the existing single try/catch around operation and refresh. Rejected because it can label completed operations as failed.

3. Keep empty-state next steps textual unless the existing action is naturally local to the panel.
   - Rationale: market data and signal empty states already have direct buttons; backtest requires a date range form in Operations, so the copy should point users there instead of adding a duplicate incomplete action.
   - Alternative considered: add a backtest button in the Recent backtest panel. Rejected because the existing form inputs are required and duplicating them would expand the UI.

## Risks / Trade-offs

- Manual refresh temporarily replaces visible data with loading placeholders -> acceptable for a small Phase 1 Dashboard and keeps state simple.
- A refresh failure after operation success may show both a successful operation summary and an API-unavailable Dashboard banner -> mitigated by keeping the messages scoped to operation versus Dashboard status.
- Empty-state copy remains English like the existing UI -> avoids unrelated localization work.

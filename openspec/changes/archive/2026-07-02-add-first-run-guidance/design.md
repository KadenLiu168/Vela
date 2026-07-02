## Context

The Dashboard already loads `GET /api/dashboard`, renders local workflow panels, and exposes market data fetch, signal generation, and backtest actions. Existing empty states cover individual panels when the API succeeds with no market data, signal, or backtest rows.

The remaining first-run gap is a concise global guide for startup states: empty local market data after a successful Dashboard load, and API failure caused by a missing or uninitialized local database. The backend currently normalizes unexpected database failures as generic API errors, so the frontend should avoid relying on backend-specific database error text.

## Goals / Non-Goals

**Goals:**
- Add a lightweight Dashboard guidance surface for first-run local setup.
- Point users to local database initialization when Dashboard data cannot load.
- Point users to market data fetching when Dashboard loads with zero local market rows.
- Keep existing Dashboard actions available for experienced users.
- Keep copy local-only and free of login, account, multi-user, deployment, or hosting assumptions.

**Non-Goals:**
- No backend API changes.
- No database initialization automation from the web UI.
- No onboarding wizard, persisted dismissal state, user accounts, or remote deployment guidance.
- No changes to signal detail, backtest detail, or unrelated Dashboard operations.

## Decisions

- Render first-run guidance inside `DashboardPage` using existing Dashboard state.
  - Rationale: the needed signals already exist in `dashboardState`; adding a new data source would expand scope without improving COP-118.
  - Alternative considered: add a backend readiness endpoint. Rejected because COP-118 is a phase-1 frontend issue and existing API errors are enough to guide local setup.

- Treat any Dashboard load failure as a local setup/API availability case in the guidance copy.
  - Rationale: the frontend cannot reliably distinguish missing schema from stopped API or other local failures because unexpected backend errors are intentionally normalized.
  - Alternative considered: match raw database error strings. Rejected because raw details are not exposed consistently and would be brittle.

- Keep the guide non-blocking.
  - Rationale: acceptance criteria explicitly require experienced users to keep direct operation access.
  - Alternative considered: modal or wizard. Rejected because it would block the dashboard workflow.

## Risks / Trade-offs

- API failures can have causes other than missing database -> Mitigation: wording includes initializing the database and checking the local API as setup steps, while retaining the existing API error message.
- Empty market data guidance duplicates the market panel empty action -> Mitigation: the guide is concise and acts as a first-run overview; the panel still owns the direct action.

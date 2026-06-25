## Context

`apps/web` is a scoped Vite React TypeScript app with a simple `AppShell`, a single `HomePage`, and COP-84's shared API client. COP-85 needs page entry points and a base local research layout, but it does not need business data loading, backend changes, authentication, or production deployment surface.

## Goals / Non-Goals

**Goals:**
- Provide stable placeholders for Dashboard, Signal Detail, and Backtest Detail.
- Make `/` render a local research workflow dashboard as the first screen.
- Keep layout and navigation simple enough for a local single-user research tool.
- Preserve the existing API health check through the shared frontend API client.

**Non-Goals:**
- Add login, user/account navigation, teams, sharing, or production deployment links.
- Add charts, persisted dashboard data, API endpoints, or domain workflows.
- Add a routing dependency before the app needs nested routing, loaders, or route-level data APIs.

## Decisions

- Use a tiny in-app History API router instead of adding `react-router`.
  - Rationale: COP-85 only requires three route placeholders and navigation links. A dependency would add package and lockfile churn without current value.
  - Alternative considered: `react-router`. Rejected for this COP because the routing surface is static and shallow.
- Keep route placeholders in page-level React components under `apps/web/src/pages`.
  - Rationale: This matches the existing extensible source layout and gives later COPs clear files to expand.
- Let `AppShell` own the local research navigation and route metadata while page components own page content.
  - Rationale: Navigation is shared layout chrome; page content can remain focused and testable.
- Keep API health display on the Dashboard only.
  - Rationale: COP-84 established the API client integration, and the Dashboard is the natural first-screen place to show local service status without coupling detail placeholders to API calls.

## Risks / Trade-offs

- Custom route handling may need replacement when routes become nested or data-driven -> Keep the router small and isolated in `App.tsx` so a later migration is localized.
- Placeholder content can drift into speculative product UI -> Limit text to workflow-oriented local research status and page entry points.
- Direct browser refresh on nested routes depends on Vite's SPA fallback during development -> Use normal path routes and keep tests at the component/router level for this COP.

## Why

COP-85 gives the Phase 1 web app a navigable structure before business pages are filled in. The current frontend renders a single skeleton page, so Dashboard, signal detail, and backtest detail work have no stable entry points.

## What Changes

- Add client-side route handling for Dashboard, Signal Detail, and Backtest Detail placeholders.
- Make the first screen a local research workflow dashboard instead of a generic frontend skeleton message.
- Extend the existing app shell into a simple research-tool layout with navigation between the three page areas.
- Keep COP-84's shared API client behavior intact and continue showing local API health from the dashboard.
- Do not add login, multi-user, production deployment, backend API routes, charts, or business data workflows.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `web-frontend-app`: Adds frontend routing and base layout requirements for the local research workflow pages.

## Impact

- Affects `apps/web/src` React components, pages, styles, and frontend tests.
- Does not require new npm dependencies.
- Does not change backend code, API client contracts, package management, or deployment behavior.

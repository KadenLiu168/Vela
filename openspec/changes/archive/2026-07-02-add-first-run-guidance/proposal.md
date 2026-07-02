## Why

First-time local users can land on the Dashboard before the local SQLite database has been initialized or before market data has been fetched. The current UI has per-panel empty states, but it lacks a lightweight first-run guide that clearly points users to the next local setup step without blocking normal operation.

## What Changes

- Add a Dashboard first-run guidance surface for local startup states.
- When Dashboard data loads successfully but market data is empty, show a concise first-run next-step prompt to fetch market data.
- When Dashboard data cannot load because the local API/database is unavailable or uninitialized, keep the Dashboard usable and show guidance to initialize the local database, then fetch market data.
- Keep experienced-user operations available; guidance must not block direct Dashboard actions.
- Keep copy local-only and avoid login, multi-user, hosting, deployment, or remote setup assumptions.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-frontend-app`: Add first-run guidance behavior to the Dashboard for missing local database/data startup states.

## Impact

- Affected code: `apps/web/src/pages/DashboardPage.tsx`, `apps/web/src/App.test.tsx`, and Dashboard styling in `apps/web/src/styles.css`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` through a focused delta spec.
- No backend API contract changes.
- No new runtime dependencies.

## Why

COP-89 needs the Dashboard to show the current strategy configuration summary so the local research workflow exposes the active strategy assumptions before users inspect signals or backtests.
The backend already serves the real YAML-backed strategy summary through the dashboard aggregate API, but the frontend currently renders only a partial strategy panel.

## What Changes

- Expand the Dashboard strategy panel to show the active strategy id/version, momentum window summary, score weights, Top N selection, defensive asset, and transaction cost summary.
- Keep the summary read-only with no edit controls or configuration mutation path.
- Continue sourcing strategy data from the existing `GET /api/dashboard` response, which is backed by the config API serialization and YAML configuration loading service.
- Add frontend tests that prove the Strategy panel renders the required configuration fields from API data and does not expose an edit entry point.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add Dashboard behavior for displaying the current read-only strategy configuration summary from real dashboard aggregate API data.

## Impact

- Affected code: `apps/web/src/api/client.ts`, `apps/web/src/pages/DashboardPage.tsx`.
- Affected tests: `apps/web/src/App.test.tsx` and any focused frontend API/page tests needed to validate rendering.
- Affected specs: `openspec/specs/web-frontend-app/spec.md`.
- APIs: no endpoint shape change is intended; the existing dashboard aggregate `strategy` object already carries the required fields.
- Dependencies: no new runtime or development dependency.

## Why

Dashboard already shows latest signal state and includes a disabled generate-signal entry point, but users cannot trigger the existing local signal generation workflow from the frontend. COP-100 needs the Dashboard to start signal generation through the real API and refresh the latest signal state after completion.

## What Changes

- Add a shared frontend API client helper for `POST /api/strategy-signals/generate`.
- Enable the Dashboard generate-signal action from the latest signal empty state and operations panel.
- Show an in-progress state while generation is pending and prevent duplicate submissions.
- Reload the Dashboard aggregate after successful generation so latest signal state reflects the backend database.
- Add frontend tests and local API integration validation for the signal generation action path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Dashboard gains a generate-signal action backed by the shared API client and local API/SQLite validation.

## Impact

- Frontend API client: `apps/web/src/api/client.ts`
- Dashboard page: `apps/web/src/pages/DashboardPage.tsx`
- Frontend tests: `apps/web/src/api/client.test.ts`, `apps/web/src/api/client.integration.test.ts`, `apps/web/src/App.test.tsx`
- OpenSpec: `openspec/specs/web-frontend-app/spec.md`

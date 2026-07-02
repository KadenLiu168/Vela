## Why

Dashboard users can complete local workflow operations, but the page still lacks an explicit manual refresh control and some empty states point to a nearby operation only indirectly. Operation success also depends on the follow-up refresh succeeding, which can hide a completed action behind a refresh failure.

## What Changes

- Add a manual Dashboard refresh action that reloads `GET /api/dashboard` through the shared frontend API client.
- Keep successful operation feedback visible when a post-operation Dashboard refresh fails, while surfacing the Dashboard refresh failure separately.
- Align Dashboard empty state copy with the next local action users can take from the Dashboard.
- Add focused frontend tests for manual refresh, post-operation refresh behavior, and empty state copy.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Extend Dashboard refresh and empty state behavior for manual refresh, post-operation refresh failure handling, and next-action-aligned empty state copy.

## Impact

- Affected code: `apps/web/src/pages/DashboardPage.tsx`, `apps/web/src/App.test.tsx`, and small Dashboard styling if needed.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via this change's delta spec.
- API impact: none; the frontend continues using existing shared client helpers and existing endpoints.
- Dependency impact: none.

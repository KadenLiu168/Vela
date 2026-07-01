## Why

COP-101 needs the web frontend to expose a real latest signal detail page instead of the current placeholder. The page should let a local research user inspect the final persisted strategy signal outcome returned by the structured latest signal API.

## What Changes

- Replace the Signal Detail placeholder route with a latest strategy signal detail page backed by `GET /api/strategy-signals/latest`.
- Add a shared frontend API client helper and response types for the latest strategy signal endpoint.
- Render signal date, config version, result, fallback status, generated timestamp, and a clear empty state when no successful signal exists.
- Keep the first version focused on final signal metadata and avoid candidate ranking diagnostics.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Add latest signal detail page behavior backed by the real latest strategy signal API.

## Impact

- Frontend API client: `apps/web/src/api/client.ts`
- Signal detail page and routing/navigation: `apps/web/src/pages/SignalDetailPage.tsx`, `apps/web/src/App.tsx`
- Frontend tests: `apps/web/src/api/client.test.ts`, `apps/web/src/App.test.tsx`
- OpenSpec web frontend specification: `openspec/specs/web-frontend-app/spec.md`

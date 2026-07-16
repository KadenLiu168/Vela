## Why

The web AppShell currently renders the global brand (`Vela Research`) as an `<h1>` in the banner while each routed page also renders its own page-level `<h1>` inside `<main>`. This creates two top-level headings per page and weakens the document outline for assistive navigation.

## What Changes

- Change the AppShell brand text from a heading to non-heading text while preserving the existing visual treatment.
- Replace the broad `.app-header h1` style hook with a dedicated brand-title class so the brand styling is no longer tied to heading semantics.
- Update the web frontend heading contract so the AppShell banner must not contribute an extra `<h1>`; the routed page remains the single page identity heading.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Tighten the AppShell/page heading requirement so the AppShell brand is non-heading text and every rendered page exposes exactly one document-level `<h1>` for the page identity.

## Impact

- Affected code: `apps/web/src/components/AppShell.tsx`, `apps/web/src/styles.css`.
- Affected spec: `openspec/specs/web-frontend-app/spec.md`.
- No API, dependency, database, or backend behavior changes.

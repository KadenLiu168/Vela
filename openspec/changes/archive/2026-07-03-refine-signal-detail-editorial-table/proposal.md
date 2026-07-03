## Why

The Signal Detail page already shows the latest signal metadata and target holdings, but its metadata block and table styling are flatter and less editorial than the Dashboard cards refined in recent frontend work. COP-133 aligns this read-only detail view with `DESIGN.md` using the existing warm-neutral data product visual language.

## What Changes

- Refine Signal Detail metadata styling so the compact list reads as an editorial data block with clear label/value hierarchy.
- Refine the Target holdings section and table container using existing Graphite, Steel, Slate, Mist, Fog, Ash, and Canvas tokens.
- Improve table header, row divider, numeric column readability, and horizontal-scroll container visuals while preserving mobile horizontal scrolling.
- Preserve the existing Signal Detail API usage, route, DOM semantics, positions rendering data, and read-only behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add Signal Detail visual alignment requirements for metadata and target holdings table styling.

## Impact

- Affected code: `apps/web/src/styles.css`
- Affected OpenSpec capability: `web-frontend-app`
- No API, route, signal API call, positions data rendering, sorting, filtering, pagination, dependency, or business logic changes.

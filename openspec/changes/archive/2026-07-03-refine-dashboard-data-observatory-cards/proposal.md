## Why

The Dashboard overview currently reads closer to a default admin dashboard than the editorial data observatory direction documented in `DESIGN.md`. COP-131 aligns the existing Dashboard information cards with the established flat, warm-neutral visual language without changing Dashboard behavior.

## What Changes

- Refine the Dashboard overview grid and panel styling to use Ash, Fog, Canvas, and Mist surfaces with no card shadow.
- Adjust Dashboard panel padding, gaps, borders, radii, and typography weights to better match the DESIGN.md hierarchy: Graphite headings, Steel body copy, and Slate metadata.
- Refine metric rows and metric blocks so the market overview and workflow panels feel like flat data cards rather than blue admin widgets.
- Preserve existing Dashboard DOM semantics, data loading, API usage, routes, operations, and information architecture.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add Dashboard visual alignment requirements for overview cards and workflow grid styling.

## Impact

- Affected code: `apps/web/src/styles.css`
- Affected OpenSpec capability: `web-frontend-app`
- No API, route, data loading, operation behavior, package dependency, or business logic changes.

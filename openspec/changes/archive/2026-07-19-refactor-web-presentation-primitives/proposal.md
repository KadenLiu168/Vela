## Why

The web frontend repeats the same description-list item implementation across four pages and keeps testable presentation logic inside large page modules. Equity-curve geometry also duplicates chart dimensions between SVG markup and coordinate calculations, making small visual changes harder to verify safely.

## What Changes

- Introduce one shared `DescriptionItem` component for canonical `<dt>/<dd>` rendering across Dashboard, ETF Detail, Signal Detail, and Backtest Detail, with a `ReactNode` value contract so linked values do not bypass the primitive.
- Keep the page-specific `Metric`, `MetricCard`, and `StatusPillBadge` implementations local until they have a second real consumer; this change does not merge visually or semantically distinct components.
- Preserve generic scalar formatting in `utils/formatters.ts` while moving presentation-specific formatter logic into page-domain pure modules that can be unit-tested without exporting non-components from page modules.
- Extract Equity Curve dimensions and pure geometry calculations into a dedicated module, using one chart constant as the source of truth for both SVG rendering and coordinate calculations.
- Add focused direct unit tests for ETF Trend and Equity Curve geometry, while retaining page-level tests for empty, single-point, multi-point, and hover behavior.
- Preserve current routes, API contracts, rendered copy, visual hierarchy, and chart behavior.
- Defer a generic multi-chart geometry framework until a third chart demonstrates stable shared requirements.

## Capabilities

### New Capabilities

- `web-presentation-primitives`: Defines canonical description-list rendering, presentation formatter boundaries, and independently testable chart-geometry modules for the React frontend.

### Modified Capabilities

None. Existing user-visible behavior remains unchanged.

## Impact

- Affected frontend areas: `apps/web/src/components/`, the four page modules, page-domain formatter modules, ETF Trend geometry, Equity Curve geometry, and Vitest coverage.
- Existing CSS selectors and design tokens remain unchanged.
- No backend, database, API, routing, dependency, or deployment changes.
- The refactor must remain compatible with React Fast Refresh by keeping page-module exports component-only.

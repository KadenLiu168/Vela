## Why

The Backtest Detail metrics, equity curve, and parameters areas still read as generic compact panels rather than the flat editorial data dashboard card system defined in `DESIGN.md`. COP-134 refines those visual surfaces so persisted backtest results feel consistent with the rest of the Vela web app without changing data loading, formatting, routing, or chart path behavior.

## What Changes

- Refine Backtest Detail metric cards with tokenized data-card surfaces, typography, spacing, and readable numeric hierarchy.
- Refine the hand-written equity curve card and summary block so the chart uses the `DESIGN.md` Ember/Brass accent language instead of blue-style chart treatment.
- Refine the parameters block so JSON remains readable in a tokenized surface consistent with the page.
- Preserve existing Backtest Detail API calls, route structure, metric formatting, equity curve path calculation, SVG structure, and `data-testid="equity-curve-line"`.
- Do not add dependencies, chart libraries, or large UI frameworks.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Backtest Detail visual presentation must align metrics, equity curve, and parameters with the existing `DESIGN.md` data dashboard card language while preserving behavior.

## Impact

- Affected code: `apps/web/src/styles.css` Backtest Detail visual selectors, with `apps/web/src/pages/BacktestDetailPage.tsx` kept behaviorally stable unless a minimal styling hook is required.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via this change's delta spec.
- APIs/routes/business logic: no changes.
- Dependencies: no changes.

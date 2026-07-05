## Why

The dashboard grid currently uses 4 columns, but the bottom row contains only three panels (Signal, Backtest, Fetches). The 4th column slot in that row stays empty, leaving a visible whitespace block to the right of the Fetches panel. The other rows are visually balanced (Market + Strategy span to fill 4 columns, Operations spans the full row), so the imbalance appears only in the bottom row and breaks the overall rhythm of the page. The existing `web-frontend-app` spec covers dashboard workflow panel cohesion but does not pin the grid column count or per-panel spans, so a concrete spec is needed to make this layout property testable.

## What Changes

- Change `.dashboard-grid` in `apps/web/src/styles.css` from `repeat(4, minmax(0, 1fr))` to `repeat(3, minmax(0, 1fr))` so each row has 3 equal columns.
- Adjust the `grid-column` span of the top-row panels to fit a 3-column row:
  - `.market-panel` and `.strategy-panel` currently both `span 2`. Under a 3-column grid, distribute as `.market-panel` `span 1` and `.strategy-panel` `span 2` (Strategy has denser detail content and benefits from the wider slot; Market is compact and reads well in a single column).
- Update `.operations-panel` from `span 4` to `span 3` so it still spans the full row width.
- Leave `.signal-panel`, `.backtest-panel`, and `.fetch-log-panel` unspanned so they each occupy one of the 3 equal columns, filling the bottom row with no trailing whitespace.
- No markup or component changes; this is a CSS-only adjustment.

## Capabilities

### New Capabilities
None. This change adds a layout property to an existing capability, not a new capability.

### Modified Capabilities

- `web-frontend-app`: Adds a requirement that the desktop Dashboard grid uses a 3-column track layout and that the bottom-row workflow panels (Signal, Backtest, Fetches) each occupy one column so the row has no trailing whitespace. Updates the per-panel `grid-column` spans so the top row and the Operations row still fill the row width.

## Impact

- Affected code: `apps/web/src/styles.css` only (one grid template change plus per-panel `grid-column` updates).
- Affected runtime: dashboard page visual layout at `/` only.
- APIs: no change.
- Dependencies: no change.
- Breaking change: no.
- Out of scope: any other frontend pages, the `workflow-grid` (Signal Detail / Backtest Detail layouts), responsive breakpoints, dark/light theme tokens, or new dashboard content.

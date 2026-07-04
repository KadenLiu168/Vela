## Why

The web frontend has little explicit `:focus-visible` styling, so keyboard users can tab through controls without a clear focus indicator. It also jumps from the desktop layout directly to a `720px` mobile breakpoint, leaving Dashboard, Signal Detail, and Backtest Detail layouts cramped around tablet and small-desktop widths.

## What Changes

- Add a unified keyboard focus treatment for links, buttons, navigation links, and form inputs using `outline` and `outline-offset`.
- Add restrained hover and transition feedback for interactive controls without introducing shadow, bounce, or layout movement.
- Respect `prefers-reduced-motion: reduce` by removing nonessential transition behavior.
- Add intermediate responsive breakpoints around `1024px` and `900px` to stabilize Dashboard grid spans, metric card columns, equity summary columns, detail page spacing, and table/card density.
- Preserve existing routes, DOM structure, API behavior, tests, and the existing `720px` mobile behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add accessibility and responsive layout requirements for visible keyboard focus and stable tablet/small-desktop page layouts.

## Impact

- Affected code: `apps/web/src/styles.css`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via this change's delta spec.
- APIs, data loading, routing, dependencies, and business logic: no changes.

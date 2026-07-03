## Why

The frontend has accumulated several focused UI changes, and COP-136 requires a final full-site visual QA pass to catch any inconsistent styling, hardcoded visual drift, or responsive regressions before closing the frontend polish work.

## What Changes

- Audit the Dashboard, Signal Detail, Backtest Detail, AppShell/navigation, tables, cards, forms, buttons, and feedback states against `DESIGN.md`.
- Make only minimal CSS fixes needed for visual consistency, token usage, and desktop/mobile readability.
- Validate the required routes at desktop and mobile viewport sizes.
- Record scope-out follow-up observations without implementing unrelated technical debt.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-frontend-app`: Add visual consistency and responsive QA requirements for the existing frontend surfaces.

## Impact

- Affected code: `apps/web/src/styles.css` only, unless QA reveals a visual issue that cannot be fixed in CSS.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` through this change's delta spec.
- APIs, routes, business logic, and dependencies remain unchanged.

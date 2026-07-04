## Why

The current web frontend already has a restrained research-tool visual system, but the Dashboard does not consistently surface the most important workflow state and next actions first. In seeded local data, long secondary content can stretch Dashboard panels and push Operations far below the first screen, which undermines the requested simple, focused experience.

## What Changes

- Refine the Dashboard information hierarchy so current workflow status, key research metrics, and next actions are visible before secondary details.
- Fix Dashboard panel layout behavior so long history or summary content does not stretch unrelated cards or push Operations deep down the page.
- Keep the visual system minimal by reusing existing color, typography, spacing, radius, and focus tokens rather than adding a new theme or dependency.
- Make empty, error, loading, and populated states more action-oriented while preserving the local-only research workflow language.
- Align Signal Detail and Backtest Detail surfaces with the same restrained data-card treatment and responsive behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Dashboard and detail page requirements will clarify focused visual hierarchy, Dashboard operation discoverability, long-content layout resilience, and consistent local workflow state presentation.

## Impact

- Affects `apps/web/src/styles.css` and, if needed for semantic ordering, small scoped JSX structure in `apps/web/src/pages/DashboardPage.tsx`.
- No API, route, data model, shared client contract, dependency, or backend behavior changes.
- Frontend validation remains based on existing unit tests, type checking, production build, and browser/manual acceptance for Dashboard and detail routes.

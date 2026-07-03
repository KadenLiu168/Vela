## Why

Dashboard operation controls and feedback states currently use several visual dialects, including rounded action buttons and large blue, green, and orange status blocks. This diverges from `DESIGN.md`, where Dashboard UI should stay mostly achromatic, use sharp Graphite actions, and reserve Ember Orange for small accents.

## What Changes

- Normalize Dashboard operation buttons, empty-state action buttons, and the refresh action to the same 0px-radius Graphite filled/outlined action language.
- Tokenize Backtest run form controls with existing border, background, typography, spacing, and radius variables.
- Restyle `FeedbackMessage`, `.dashboard-load-state`, `.dashboard-alert`, `.operation-summary`, `.operation-guidance`, and `.operation-link` so loading, error, and success feedback no longer relies on large blue, green, or red color blocks.
- Preserve existing accessibility roles, Dashboard operations, form validation behavior, disabled/loading conditions, API calls, routes, and copy.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Dashboard UI feedback and operation controls must follow the project design language without changing Dashboard behavior.

## Impact

- Affected code: `apps/web/src/styles.css`, `apps/web/src/components/FeedbackMessage.tsx`, and focused frontend tests if needed for accessibility/behavior preservation.
- Affected specs: `openspec/specs/web-frontend-app/spec.md`.
- APIs, routing, dependencies, backend behavior, and operation business logic are not changed.

## Why

Dashboard, Signal Detail, and Backtest Detail already expose loading, empty, error, and operation status states, but their visual presentation is split across shared and page-specific selectors. COP-135 consolidates those existing states into a shared tokenized presentation so state feedback is recognizable without broad blue, green, or red blocks.

## What Changes

- Extend the shared feedback presentation for loading, info, success, and error variants using existing design tokens and narrow accents.
- Align `.empty-state` and Dashboard load-state styling with the same neutral editorial status language.
- Apply the shared empty/loading/error/status presentation to existing Dashboard, Signal Detail, and Backtest Detail states without changing state logic, copy meaning, API calls, or routes.
- Preserve `role="status"` and `role="alert"` semantics for existing `FeedbackMessage` usage.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Existing frontend status and empty-state requirements are expanded to cover shared loading, error, info, success, and empty-state presentation across Dashboard and detail pages.

## Impact

- Affected code: `apps/web/src/components/FeedbackMessage.tsx`, `apps/web/src/styles.css`, and minimal existing status markup/classes in Dashboard, Signal Detail, and Backtest Detail if needed.
- Affected specs: `openspec/specs/web-frontend-app/spec.md`.
- APIs, routing, business logic, dependencies, loading timing, error categorization, and skeleton loaders are out of scope.

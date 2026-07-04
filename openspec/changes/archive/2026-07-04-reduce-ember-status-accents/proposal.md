## Why

COP-135 consolidated shared empty, loading, error, and operation status presentation, but error and failed states still promote Ember Orange into a strong status rail. COP-142 narrows that treatment so status surfaces stay mostly achromatic and Ember remains a small functional punctuation color as described in `DESIGN.md`.

## What Changes

- Reduce Ember Orange usage in shared error and failed status surfaces by moving their primary accent rail to neutral Graphite.
- Keep empty, loading, success, info, partial, and failed states visually related through neutral surfaces, Mist borders, and restrained status accents.
- Preserve existing `FeedbackMessage` component structure, `role="alert"`, `role="status"`, `aria-live`, status text, loading behavior, API calls, and route behavior.
- Keep Ember available for existing operation/detail link underline treatment and other small accent usage.
- Do not add new state colors, skeleton loaders, or a rewritten feedback component system.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Refine shared frontend status presentation so error and failed surfaces do not rely on broad Ember accents while preserving accessibility semantics and recognizable error states.

## Impact

- Affected code: `apps/web/src/styles.css`
- Affected tests: existing `apps/web/src/App.test.tsx` loading, empty, error, partial, and failed state coverage
- Affected specs: `openspec/specs/web-frontend-app/spec.md`
- No API, route, component hierarchy, ARIA, copy, dependency, or skeleton loading changes.

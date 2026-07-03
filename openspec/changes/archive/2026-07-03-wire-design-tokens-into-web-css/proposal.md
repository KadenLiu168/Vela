## Why

The web frontend currently uses hard-coded global style values that do not expose the provided `DESIGN.md`, `tokens.json`, and `variables.css` visual foundation to application CSS. Wiring those tokens into the global stylesheet gives later frontend visual refinement issues a shared, consistent base without changing business behavior.

## What Changes

- Add the provided design token custom properties to `apps/web/src/styles.css`, covering core colors, typography, spacing, radius, layout, and surface tokens.
- Align base document typography, text color, page background, and box sizing with the design token foundation while keeping visual change intentionally small.
- Use the token foundation for safe global-style replacements where the existing values map directly to the provided neutral, surface, spacing, or radius tokens.
- Preserve existing route structure, API behavior, component DOM, and semantic status styling that has no direct design-token equivalent.
- Do not add a token build pipeline, Style Dictionary setup, UI framework, or new runtime dependency.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Adds requirements for the web frontend to expose the provided design tokens through global CSS custom properties and use them for base page typography and surfaces.

## Impact

- Affected code: `apps/web/src/styles.css`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via this change's delta spec.
- Validation: existing frontend lint, typecheck, test, and build scripts, plus OpenSpec validation.
- No API, routing, backend, data model, dependency, or business-logic impact.

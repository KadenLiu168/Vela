## Why

The web app header and navigation still read as default bordered controls, while COP-129 established the design token foundation for the editorial monochrome visual system. Refining the App Shell header now gives every page a consistent first impression before later page-level visual passes.

## What Changes

- Add focused App Shell styling hooks for the brand block, API metadata, nav container, and nav links without changing navigation data, hrefs, `aria-current`, or click behavior.
- Restyle the header toward the `DESIGN.md` editorial shell: Graphite brand typography, subdued Slate API metadata, Ash pill navigation container, and text-style nav items.
- Keep the active nav state clear but restrained using tokenized neutral colors and pill treatment.
- Preserve mobile readability by allowing the header and nav to wrap without route, API, or business-logic changes.
- Do not add icons, dropdowns, language toggles, contact buttons, new pages, new dependencies, or broader component redesigns.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Adds requirements for the App Shell header and navigation to use the tokenized editorial visual system while preserving existing navigation semantics and behavior.

## Impact

- Affected code: `apps/web/src/components/AppShell.tsx` and `apps/web/src/styles.css`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via this change's delta spec.
- Validation: existing frontend lint, typecheck, test, and build scripts, plus OpenSpec validation.
- No API, routing, nav data source, backend, data model, dependency, or business-logic impact.

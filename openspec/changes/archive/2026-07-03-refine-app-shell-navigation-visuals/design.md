## Context

COP-129 added the global design token foundation to `apps/web/src/styles.css`. The current App Shell header still uses generic bordered link buttons for navigation, which does not match `DESIGN.md` guidance for an editorial header with a warm-gray pill navigation container and text-style nav links. `AppShell.tsx` already centralizes the brand, API metadata, and navigation behavior.

## Goals / Non-Goals

**Goals:**

- Add stable class hooks for the App Shell brand block, API metadata, nav container, and nav links.
- Style the header and navigation with existing design tokens: Graphite text, Slate metadata, Ash/Mist neutral surfaces, PolySans nav typography, and pill-shaped navigation.
- Preserve current nav labels, hrefs, `aria-current`, `onNavigate` behavior, and route semantics.
- Keep mobile header/nav readable by allowing wrapping and full-width pill behavior where needed.

**Non-Goals:**

- No new nav items, dropdowns, chevrons, language toggle, contact button, or icons.
- No changes to route definitions, nav data source, API base URL source, or business logic.
- No broader dashboard/card/form visual pass.
- No new dependencies or UI framework.

## Decisions

1. Add class names to `AppShell.tsx` for styling hooks.
   - Alternative: target `div`, `span`, `nav`, and `a` descendants from `.app-header`.
   - Rationale: dedicated classes keep this visual change scoped and avoid fragile descendant selectors while preserving DOM semantics and behavior.

2. Implement the navigation as a tokenized pill container with text-style links.
   - Alternative: keep individual bordered buttons and only adjust colors.
   - Rationale: the issue explicitly asks to move toward the `DESIGN.md` Navigation Pill Container, so the grouped pill is the smallest meaningful visual change.

3. Use a restrained active state.
   - Alternative: use Ember Orange or a strong CTA fill.
   - Rationale: `DESIGN.md` reserves orange for accents and says active text links can use subtle color shifts. A neutral pill active state preserves clarity without overusing accent color.

4. Validate through existing behavior tests plus browser smoke check.
   - Alternative: add CSS snapshot tests.
   - Rationale: current tests validate navigation behavior and route semantics. A quick browser render check better covers the visual risk without adding brittle snapshots.

## Risks / Trade-offs

- Header changes affect every page first impression -> mitigate by changing only App Shell classes and leaving content layouts untouched.
- Added class names could accidentally alter tests if semantics change -> mitigate by keeping text, roles, hrefs, and `aria-current` unchanged.
- Pill navigation can wrap awkwardly on narrow screens -> mitigate with flex wrapping and mobile-specific full-width alignment.

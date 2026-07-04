## Context

The frontend uses a single global stylesheet at `apps/web/src/styles.css`. Current interactive elements rely mostly on browser defaults and custom visual states, with no consistent `:focus-visible` treatment. Responsive layout currently has a single `max-width: 720px` mobile breakpoint while desktop grid rules remain active through tablet and small-desktop widths.

## Goals / Non-Goals

**Goals:**

- Make keyboard focus clearly visible across links, buttons, navigation items, and date inputs.
- Add restrained hover feedback that fits the flat warm-neutral visual system and does not use `box-shadow`.
- Add intermediate breakpoints so Dashboard, Signal Detail, and Backtest Detail remain readable around `900px` and `1024px`.
- Preserve the current `720px` mobile layout and `1200px+` desktop layout.

**Non-Goals:**

- No React DOM, route, API, data formatting, or business logic changes.
- No complex page entrance animation or layout motion.
- No new CSS framework, component library, or dependency.

## Decisions

- Use CSS-only implementation in `styles.css`.
  - Rationale: the issue is visual and responsive; current DOM already exposes semantic links, buttons, and inputs.
  - Alternative considered: add component-level focus classes. Rejected because it would widen the change and duplicate global behavior.

- Use `outline` and `outline-offset` for `:focus-visible`.
  - Rationale: this satisfies the no-shadow design principle and remains visible on flat Canvas, Fog, Ash, and Graphite surfaces.
  - Alternative considered: `box-shadow` focus rings. Rejected because the visual system avoids shadows.

- Use two intermediate breakpoint bands: `max-width: 1024px` and `max-width: 900px`.
  - Rationale: `1024px` catches common tablet landscape and small desktop widths; `900px` catches narrower tablet portrait before the existing `720px` mobile rules take over.
  - Alternative considered: a single `max-width: 960px` breakpoint. Rejected because Dashboard grid density and detail page card density need slightly different reductions.

- Keep hover feedback to color/background/border transitions only.
  - Rationale: subtle state change improves affordance without bounce, translation, or heavy motion.
  - Alternative considered: transform-based lift. Rejected because it adds visible movement and risks layout polish regressions.

## Risks / Trade-offs

- Focus rings may look visually assertive on dark active nav pills -> Use existing Ember and Canvas tokens so active dark surfaces still have sufficient contrast.
- Tablet breakpoints can reduce information density -> Change only grid columns, spans, gaps, and padding so content remains intact.
- CSS-only visual verification is limited in unit tests -> Validate with test/typecheck/build, OpenSpec validation, and browser screenshots at representative widths.

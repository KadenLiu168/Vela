## Context

`DESIGN.md` defines a restrained Dashboard visual system: Graphite filled and outlined actions, 0px button radius, tokenized warm-neutral surfaces, and Ember Orange only as a small accent. The current Dashboard action and feedback CSS predates that system and still uses rounded controls plus broad blue, green, and orange state blocks.

## Goals / Non-Goals

**Goals:**

- Align Dashboard action buttons, empty-state actions, form controls, and operation feedback with existing design tokens.
- Preserve existing Dashboard behavior, accessibility roles, API calls, routing, validation logic, and disabled/loading conditions.
- Keep implementation small and CSS-first.

**Non-Goals:**

- No changes to market fetch, signal generation, or backtest API calls.
- No changes to routing, business logic, form validation logic, or operation state handling.
- No new toast, modal, UI framework, or dependency.
- No broad redesign outside the COP-132 Dashboard feedback/action styling scope.

## Decisions

- Use CSS custom properties already present in `apps/web/src/styles.css` for color, spacing, typography, and radius. Add only local component-level tokens if a repeated value is needed for this issue.
- Style action buttons through existing selectors (`.dashboard-refresh-action`, `.operation-list button`) so JSX and disabled/loading conditions remain unchanged.
- Keep `FeedbackMessage` role selection unchanged (`error` as `alert`, all other variants as `status`) and use variant classes only for visual treatment.
- Represent success, loading, info, and error feedback with neutral surfaces, Graphite text, Mist borders, and narrow Ember/Brass accents instead of large chromatic fills.
- Keep operation summaries as `FeedbackMessage` wrappers to avoid changing component structure or test-visible content.

## Risks / Trade-offs

- Visual-only acceptance is harder to assert through unit tests -> use focused DOM/class/role tests plus build, lint, typecheck, and manual CSS review.
- Some legacy selectors are shared by detail pages -> keep changes scoped to Dashboard-specific classes where possible and preserve generic `FeedbackMessage` semantics.
- CSS-only normalization may not create semantic primary/secondary button props -> acceptable because adding a button abstraction would exceed the requested minimal scope.

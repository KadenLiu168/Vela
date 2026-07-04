## Context

`apps/web` is a Vite/React frontend for a local ETF research workflow. The active visual system lives in `apps/web/src/styles.css` and already defines a restrained graphite/canvas/ash/fog/brass/ember token set, editorial page headings, focus-visible styling, and responsive breakpoints.

Browser inspection of the current Dashboard with seeded local data showed a layout failure: long `Recent fetches` content stretches the second dashboard row, causing sibling cards to become extremely tall and pushing `Operations` far below the first screen. This makes the primary workflow actions hard to discover even though the underlying API behavior is correct.

## Goals / Non-Goals

**Goals:**

- Keep the web UI minimal, local-tool focused, and consistent with the existing token system.
- Make Dashboard status, key metrics, and next actions visible before secondary historical details.
- Prevent long secondary content from stretching unrelated Dashboard cards or hiding Operations.
- Preserve existing route behavior, API calls, state handling, accessibility roles, and local workflow copy.
- Keep Signal Detail and Backtest Detail aligned with the same focused card and state presentation where they share styling.

**Non-Goals:**

- No marketing hero, decorative illustration, landing page, account flow, or deployment language.
- No new frontend framework, component library, charting library, icon set, or runtime dependency.
- No backend, API contract, route, formatter, or data model changes.
- No broad redesign of all copy or unrelated component refactors.

## Decisions

- Use CSS-first layout corrections for Dashboard.
  - Rationale: the failure is primarily caused by grid/card sizing and content containment; CSS can correct it without touching data flow.
  - Alternative considered: replace the Dashboard grid with a new component system. Rejected because it would widen the change and risk unrelated behavior.

- Allow small scoped JSX reordering only if required to place Operations before secondary detail panels in DOM and reading order.
  - Rationale: visual order alone is not enough if keyboard and assistive-technology order still buries the primary actions.
  - Alternative considered: CSS-only visual reordering. Rejected if it would make visual order diverge from DOM order.

- Treat `Recent fetches` and dense history as bounded secondary content.
  - Rationale: history is useful but must not determine the height of the core Dashboard workflow.
  - Alternative considered: remove fetch history from the Dashboard. Rejected because existing requirements expect recent fetch log display.

- Reuse the current design tokens and status components.
  - Rationale: the project already has tokenized surfaces, focus rings, feedback states, and responsive rules; extending those keeps the result simple.
  - Alternative considered: introduce new color tokens or status components. Rejected because the requested direction is minimal and focused, not a new theme.

- Validate with existing frontend commands plus browser inspection at representative widths.
  - Rationale: unit tests cover behavior and state text, while browser inspection is needed for layout resilience and first-screen hierarchy.
  - Alternative considered: rely only on snapshots or unit tests. Rejected because the observed issue is visual layout behavior.

## Risks / Trade-offs

- Dashboard density could drop if Operations moves higher -> Keep actions compact and avoid adding explanatory blocks beyond existing state copy.
- Bounded history may hide some log details -> Preserve recent fetch content in a scrollable or capped area so data remains accessible without controlling page height.
- CSS grid changes can affect tablet layouts -> Verify desktop, `1024px`, `900px`, and mobile widths against the existing manual acceptance checklist.
- JSX reordering could affect tests that query by broad order -> Keep headings, labels, roles, links, and button names stable; adjust tests only for intentional layout/order expectations.

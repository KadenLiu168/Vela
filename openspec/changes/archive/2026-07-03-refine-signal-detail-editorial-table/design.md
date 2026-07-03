## Context

COP-133 targets the existing Signal Detail page visual treatment. `apps/web/src/pages/SignalDetailPage.tsx` already renders latest signal metadata, target holdings, loading/error states, and empty states using shared classes. The gap is CSS alignment with `DESIGN.md` and the Dashboard visual rules established by recent frontend issues.

Existing tokens in `apps/web/src/styles.css`, `variables.css`, and `tokens.json` already provide the required Graphite, Steel, Slate, Mist, Fog, Ash, Canvas, spacing, typography, and radius vocabulary. No new dependency or token is required.

## Goals / Non-Goals

**Goals:**

- Make the Signal Detail metadata block feel consistent with Dashboard editorial data cards.
- Make the target holdings table restrained and readable, with clear headers, hairline row separation, and readable numeric columns.
- Preserve the horizontal scrolling table wrapper on mobile and narrow screens.
- Keep empty-state styling consistent with the shared Dashboard/detail visual language.

**Non-Goals:**

- Do not modify business logic, API calls, route structure, signal API helper usage, or positions data rendering.
- Do not add sorting, filtering, pagination, controls, or new table behavior.
- Do not introduce large UI frameworks or new package dependencies.
- Do not redesign unrelated pages beyond the shared selectors already used by the Signal Detail page.

## Decisions

1. Keep the implementation CSS-only.
   - Rationale: the existing JSX exposes the required styling hooks and COP-133 is a visual refinement issue.
   - Alternative considered: adding wrapper markup or column-specific classes. Rejected because table column targeting can be handled with CSS selectors without changing rendering data.

2. Reuse existing design tokens.
   - Rationale: current tokens cover the requested color, surface, radius, spacing, and type hierarchy.
   - Alternative considered: adding detail-table-specific tokens. Rejected as unnecessary token expansion for a single scoped refinement.

3. Scope the strongest refinements to `.detail-page` and holdings selectors.
   - Rationale: `.compact-list` and `.empty-state` are shared with Dashboard; page-scoped overrides reduce risk to other pages while letting Signal Detail match the established language.
   - Alternative considered: changing global `.compact-list` and `.empty-state` defaults. Rejected because COP-133 should not restyle Dashboard or other panels.

4. Use CSS column selectors for numeric holdings columns.
   - Rationale: target weight, rank, and score readability can improve through right alignment and tabular numerals without altering the `positions.map` rendering or adding data attributes.
   - Alternative considered: changing JSX to attach classes to cells. Rejected because that touches rendering code without being necessary for this issue.

## Risks / Trade-offs

- CSS column selectors are tied to the existing holdings table column order. This is acceptable because COP-133 explicitly preserves the current positions rendering data and table structure.
- Visual validation is partly subjective. Mitigation: map styling directly to `DESIGN.md` tokens and run frontend validation plus OpenSpec validation.

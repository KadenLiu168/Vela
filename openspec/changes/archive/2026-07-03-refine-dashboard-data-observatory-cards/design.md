## Context

COP-131 targets the Dashboard route overview cards and workflow grid styling. The current Dashboard already renders the required market, strategy, signal, backtest, fetch history, and operations sections from the aggregate API response; the gap is visual alignment with `DESIGN.md`.

Existing tokens in `apps/web/src/styles.css`, `variables.css`, and `tokens.json` already define the required color, spacing, typography, surface, and radius vocabulary. The implementation can therefore remain a surgical CSS-only adjustment.

## Goals / Non-Goals

**Goals:**

- Align Dashboard cards with the flat data observatory style: warm neutral surfaces, no shadow, restrained borders, and editorial data hierarchy.
- Use Graphite for headings and key values, Steel for body/data values, and Slate for metadata labels.
- Use existing Ash, Fog, Canvas, and Mist surface tokens for the Dashboard grid, panels, metrics, and nested lists.
- Preserve desktop and mobile readability without changing Dashboard DOM structure.

**Non-Goals:**

- Do not change API calls, response usage, route structure, data loading, operation behavior, or business logic.
- Do not add new Dashboard features or controls.
- Do not introduce new UI frameworks or package dependencies.
- Do not redesign unrelated pages or detail-page components.

## Decisions

1. Keep the implementation CSS-only.
   - Rationale: COP-131 is a visual alignment issue and the existing JSX already exposes stable classes for the targeted regions.
   - Alternative considered: editing component markup to add wrappers or metadata elements. Rejected because it increases behavior and DOM risk without being necessary.

2. Reuse existing design tokens instead of adding new tokens.
   - Rationale: `--color-*`, `--surface-*`, spacing, radius, and typography tokens already cover the requested Ash/Fog/Canvas/Mist and Graphite/Steel/Slate hierarchy.
   - Alternative considered: adding Dashboard-specific tokens. Rejected because the current issue can be completed without expanding the token surface.

3. Use flat panel differentiation through surface contrast and hairline borders.
   - Rationale: `DESIGN.md` explicitly avoids shadows and blue admin styling. Ash outer panels with Fog nested data blocks and Mist borders create hierarchy without elevation.
   - Alternative considered: keeping Canvas panels with only border changes. Rejected because it does not move the Dashboard far enough from the default admin-card look.

4. Preserve the existing responsive breakpoints.
   - Rationale: The current mobile breakpoint already collapses the grid safely; COP-131 only requires that readability not regress.
   - Alternative considered: adding new breakpoints. Rejected as unnecessary scope expansion.

## Risks / Trade-offs

- Visual-only validation is partly subjective -> Mitigation: map changes directly to DESIGN.md tokens and acceptance criteria, then run lint/typecheck/test/build and OpenSpec validation.
- Global CSS selectors can affect adjacent pages -> Mitigation: limit edits to COP-131 selectors and avoid changing shared detail-page styles except where existing Dashboard selectors already apply.
- Larger card padding can reduce above-the-fold density -> Mitigation: use existing `--spacing-20` and `--spacing-16` values rather than full `--card-padding` everywhere.

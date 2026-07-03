## Context

Backtest Detail already renders persisted run metadata, metric cards, a hand-written SVG equity curve, empty/single-point chart states, and a formatted parameters block. `DESIGN.md` defines a flat editorial data dashboard card language: warm neutral surfaces, tokenized typography, no shadows, and Ember/Brass chart accents. The current Backtest Detail styles use the same code path and tests as the rest of the frontend, so this change should be a CSS-focused visual refinement.

## Goals / Non-Goals

**Goals:**

- Align Backtest Detail metrics, equity curve, chart summary, and parameters with `DESIGN.md` data dashboard card styling.
- Use existing CSS custom properties for colors, spacing, radii, typography, and surfaces.
- Keep empty and single-point equity curve states readable.
- Preserve existing DOM semantics, route behavior, API usage, formatter usage, equity curve path calculation, SVG structure, and `data-testid="equity-curve-line"`.

**Non-Goals:**

- No new chart library, UI framework, dependency, route, API call, or formatter.
- No changes to backtest calculation, equity curve point filtering, path generation, or parameter JSON formatting.
- No changes to COP-135 or unrelated page areas.

## Decisions

1. Refine Backtest Detail through scoped CSS selectors.
   - Rationale: The request is visual, and existing markup already exposes the needed hooks.
   - Alternative considered: Add new components or wrapper markup. Rejected because it increases behavioral and DOM risk without improving the acceptance criteria.

2. Use existing tokens instead of adding new tokens.
   - Rationale: `styles.css` already exposes Graphite, Steel, Slate, Mist, Canvas, Fog, Ash, Ember, Brass, data card radius, spacing, and typography tokens needed for this issue.
   - Alternative considered: Add Backtest-specific CSS variables. Rejected because current tokens are sufficient and the issue asks to avoid style sprawl.

3. Treat the equity curve line as the primary chart accent and set it to Brass.
   - Rationale: `DESIGN.md` identifies Brass as the secondary accent for chart strokes and decorative SVG lines, with Ember as restrained punctuation.
   - Alternative considered: Use Ember Orange for the line. Rejected because Brass is the more explicit chart-stroke token and avoids over-promoting Ember.

4. Preserve existing tests and add no visual snapshots.
   - Rationale: Current tests already guard Backtest Detail content, empty/single-point states, API calls, and the stable `equity-curve-line` test id. CSS-only refinements are better validated with lint/typecheck/test/build and OpenSpec validation than brittle snapshots.

## Risks / Trade-offs

- Visual CSS changes are not deeply asserted by current tests -> Mitigate by limiting changes to tokenized CSS selectors and preserving tested markup/behavior.
- Five metric cards can become cramped on narrow widths -> Mitigate with responsive `auto-fit` grid behavior while keeping existing mobile one-column fallback.
- Chart accent could become less prominent than the prior color -> Mitigate with a slightly stronger tokenized stroke width and rounded stroke caps without changing the SVG path or structure.

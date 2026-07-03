## Context

Backtest Detail renders the equity curve as an inline SVG in `BacktestDetailPage.tsx`. The chart already filters invalid `net_value` rows, draws a Brass path with `data-testid="equity-curve-line"`, and has separate empty and single-point states. `DESIGN.md` reserves Ember Orange for restrained chart highlights and small accents, not primary fills.

## Goals / Non-Goals

**Goals:**

- Add small Ember Orange highlights to multi-point equity curves.
- Keep the existing Brass path behavior and `data-testid="equity-curve-line"` stable.
- Reuse the existing SVG geometry so path and highlight coordinates cannot drift.
- Keep empty and single-point states from rendering SVG path or highlight artifacts.

**Non-Goals:**

- Do not add a charting library or dependency.
- Do not redesign the Backtest Detail page or chart summary.
- Do not change the Backtest Detail API contract.
- Do not use Ember Orange as the main line color or a large filled area.

## Decisions

1. Share chart coordinate calculation between the line path and highlight circles.
   - Alternative: duplicate the x/y math inside the highlight code.
   - Rationale: a small helper keeps coordinates consistent while preserving the existing path command output.

2. Highlight the last point plus min/max net-value points, deduped by curve index.
   - Alternative: highlight every point.
   - Rationale: highlighting every point would turn Ember into a dominant chart color. End/min/max markers give useful visual anchors while staying restrained.

3. Render highlight circles only in the multi-point SVG branch.
   - Alternative: add a marker to the single-point state.
   - Rationale: current single-point behavior intentionally avoids drawing a multi-point chart, and COP-139 requires preserving that state.

4. Style highlights with the existing `--color-ember-orange` token.
   - Alternative: hard-code `#ff682c`.
   - Rationale: the app already exposes the design token in `styles.css`, and token usage keeps the visual system centralized.

## Risks / Trade-offs

- Shared geometry helper changes could accidentally alter path output -> keep the same chart constants and number formatting, and assert the existing path test still passes.
- Highlighting min, max, and end can produce fewer than three circles when points overlap -> dedupe by index to avoid stacked circles and keep the visual clean.
- Ember points may become visually too strong -> use small radii and CSS token styling only for circles, leaving the line Brass.

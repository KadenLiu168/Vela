## Context

The ETF trend chart shipped in `add-etf-price-trend-chart` (now live as the `etf-price-trend`
capability) renders hover by mapping one `<rect onMouseEnter>` per data point
(`EtfDetailPage.tsx:262-273`). `hoverIndex` is plain `useState` with no memoization, so each `onMouseEnter`
re-runs `getValidTrendPoints` (O(n) `flatMap`), `Math.min`/`Math.max` over the spread series (O(n)),
`linePath` string construction (O(n)), and React reconciliation of all `n` rect elements (O(n)). The
hover bands use a cell grid (`bandWidth = drawableWidth / n`) while points use an end-to-end grid
(`x(i) = paddingLeft + drawableWidth * i / (n-1)`), so band centers coincide with points only at the
series midpoint; at the edges the highlighted circle lands half a band off the cursor -- visible on
the short series the chart was validated against.

The original design deferred core-layer down-sampling (LTTB/stride) on the assumption that interaction
stays acceptable below ~2000 points. That assumption holds for the data layer but not for the
per-point-rect front-end implementation, which degrades in the few-hundred-point range. This change
fixes the hover hit semantics and makes interaction cost independent of series length, leaving
down-sampling as a future path-fidelity concern rather than a hover blocker.

The chart has no chart-library dependency and intentionally mirrors the hand-written SVG pattern of
`BacktestDetailPage`'s equity curve (which has no hover). The equity-curve chart offers no reusable
pointer-to-index helper, so one is introduced here.

## Goals / Non-Goals

**Goals:**

- Hover hit detection cost independent of series length: O(1) DOM nodes and O(1) work per pointer move,
  for series up to the largest realistic `Max` horizon (~3000+ daily points).
- Correct hover hit semantics: the highlighted point is the one whose x-coordinate is nearest the
  pointer, clamped to the series bounds -- no half-band misalignment at the edges.
- Testable hover resolution without depending on jsdom layout (which returns all-zero
  `getBoundingClientRect`).
- No backend, API contract, dependency, or database changes.

**Non-Goals:**

- No lossy down-sampling (LTTB / fixed stride). Remains deferred for path fidelity on exceptionally
  long series (>~10k points); not on the hover-critical path after this change.
- No touch / tap-to-read interaction. Hover is pointer-driven; touch devices fall back to the
  latest-point readout (the existing `onMouseLeave` semantics). Listed as a known limitation.
- No change to the line rendering, axis labeling, single-point, or empty-state behavior.
- No chart library introduction.

## Decisions

### D1: Single overlay `<rect>` + `onMouseMove`, not one rect per point

Replace the per-point `<rect onMouseEnter>` array with one transparent `<rect>` covering the plot area
whose `onMouseMove` resolves the nearest index. DOM nodes for hover drop from O(n) to O(1); React no
longer reconciles `n` keyed rects on each hover state change.

Alternatives considered:
- **Memoize the per-point rect array only**: keeps O(n) DOM nodes (memory + initial render cost) and
  leaves the half-band misalignment unfixed. Rejected -- it papers over re-render cost without
  addressing either root defect.
- **Virtualize the hover rects**: over-engineering for a single-series line chart. Rejected.

### D2: Point-grid hit math, not band-cell math

Resolve the index with the point grid `pointSpacing = drawableWidth / (pointCount - 1)`:
`index = clamp(round((viewBoxX - paddingLeft) / pointSpacing), 0, pointCount - 1)`. Because points are
placed on this exact grid, `round` yields the point whose x-coordinate is nearest the cursor, and the
highlighted circle lands directly under the pointer at every index -- eliminating the half-band offset
inherent to the current `drawableWidth / n` cell grid.

Alternatives considered:
- **Keep the cell grid, use band centers**: still misaligned at the edges (band center == point only at
  the midpoint). Rejected.
- **Binary search nearest point by x**: correct but unnecessary; the uniform point grid makes the
  closed-form `round` exact and cheaper. Rejected.

### D3: Screen-to-viewBox conversion via `getBoundingClientRect`

The SVG renders through `viewBox="0 0 640 260"` with CSS-driven display size, so `event.clientX` (CSS
pixels) must be mapped to viewBox units before D2's math applies:
`viewBoxX = (clientX - rect.left) * (TREND_CHART.width / rect.width)`. Omitting this scales the hit
coordinate to the wrong space and misaligns the entire chart. This conversion is the only part of hover
resolution that depends on live layout; it is kept in the event handler, separate from the pure
`indexFromX` helper so the helper remains unit-testable without a DOM.

### D4: Memoize series geometry and split hover-dependent subtrees

The overlay (D1) removes O(n) DOM and reconciliation, but the series-derived computation --
`chartPoints`, `minPrice`/`maxPrice`, `linePath` -- is recomputed on every render because `hoverIndex`
is `useState` at the `TrendChart` level. Wrap these in `useMemo` keyed only on `points` (never
`hoverIndex`), and split the hover-dependent nodes -- the highlight `<circle>` and the readout `<dl>` --
into a child component that subscribes to `hoverIndex`. Result: a pointer move re-renders O(1) nodes
and skips all O(n) series derivation.

Alternatives considered:
- **Overlay only, no memo**: DOM is O(1) but `linePath` (a 3000-segment string) is rebuilt on every
  move -- CPU still O(n) per hover. Rejected; memo is required to realize the O(1) claim.
- **`useRef` + imperative DOM mutation for the highlight**: faster but abandons React's declarative
  model and breaks the existing `data-testid="trend-highlight"` contract the tests rely on. Rejected.

### D5: Extract `indexFromX(viewBoxX, pointCount)` as a pure helper, test it directly

jsdom's `getBoundingClientRect` returns all zeros, so an `onMouseMove` handler that reads layout cannot
be driven to a deterministic index in unit tests. Extract the index math (D2 + clamp) into a pure
function taking `viewBoxX` and `pointCount` (plus the constant padding/width), and unit-test it
covering: midpoint alignment, both edge clamps, and the half-band-offset regression (assert the
resolved index tracks the nearest point, not the band cell). The event handler reduces to the D3
conversion plus a call to this helper.

### D6: No down-sampling in this change

With O(1) hover (D1 + D4), the interaction-degradation threshold moves from the few-hundred-point range
to the tens-of-thousands range. LTTB/stride down-sampling is lossy (alters trend shape) and would
change the endpoint contract (a `max_points` param). It is not justified to fix a hover problem that
this change already solves. Down-sampling remains a documented future option for path fidelity on
exceptionally long series, decoupled from hover.

## Risks / Trade-offs

- [Screen-to-viewBox conversion bug] -> A wrong scale factor misaligns hover across the whole chart.
  Mitigation: the conversion is isolated in the event handler; the index math is the pure, unit-tested
  `indexFromX`. Edge and midpoint cases are covered by direct helper tests.
- [Test migration breaks existing coverage] -> The `getAllByTestId("trend-hover-band")` (count 3) +
  `fireEvent.mouseEnter` case no longer applies. Mitigation: replace with `indexFromX` unit tests plus
  an overlay `mouseMove` end-to-end test that mocks `getBoundingClientRect` (or drives the helper) to
  assert the readout and highlight track the resolved point.
- [Stale memo from wrong dependency] -> `linePath` could freeze on a stale series. Mitigation: `useMemo`
  keys are `points` only; `hoverIndex` is never a geometry-memo key. The series is the sole input to
  geometry.
- [Touch devices have no hover] -> Pointer-driven hover is absent on touch. Mitigation: accepted
  limitation for a Phase 1 personal-research desktop tool; touch falls back to the latest-point readout
  via the existing `onMouseLeave`/default-index path. No touch-specific work in scope.
- [Pointer move frequency] -> Rapid moves could still queue many state updates. Mitigation: the handler
  only calls `setHoverIndex` when the resolved index actually changes, so intra-band moves are no-ops;
  combined with D4's memo, each meaningful update is O(1).

## Migration Plan

Front-end-only change, no deploy or rollback complexity. Steps:
1. Add the pure `indexFromX` helper with unit tests (green before touching the component).
2. Refactor `TrendChart`: add the overlay `<rect>` + `onMouseMove`, remove the per-point rect array,
   switch hit math to the point grid, add `useMemo` for series geometry, split hover-dependent
   subtrees.
3. Rewrite the `App.test.tsx` hover cases to the overlay/`indexFromX` model.
4. Manually verify on a `Max` horizon for the oldest available ETF that a cursor sweep stays responsive
   and the highlight tracks the pointer at both edges.

Rollback: revert the two files; no schema, contract, or persisted-state involvement.

## Open Questions

- Whether to later add tap-to-pin a readout for touch devices. Out of scope here; revisit if the chart
  is used on touch. The current default-index fallback is adequate for Phase 1.

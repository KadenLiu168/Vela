## Why

The shipped ETF trend chart (`EtfDetailPage.tsx`) implements hover as one `<rect onMouseEnter>` per
data point. Two defects follow from that choice: (1) each hover toggles `hoverIndex` via `useState`
with no memoization, so every pointer crossing re-runs `getValidTrendPoints`, `Math.min/max` over the
series, `linePath` string building, and React reconciliation of all `n` rects -- O(n) per hover event,
which on a `Max` horizon for a 10y+ ETF (2500-3250 daily points) makes a single sweep across the chart
fire hundreds-to-thousands of O(n) re-renders; (2) the hover bands use a cell grid
(`drawableWidth / n`) while points use an end-to-end grid (`drawableWidth / (n-1)`), so the highlighted
circle lands half a band off the cursor at the series edges -- a visible misalignment on the small-`n`
cases the chart was actually validated against. The original design deferred core-layer down-sampling
on the assumption that interaction stays acceptable below ~2000 points, but the per-point-rect
implementation degrades well before that threshold. This change fixes the hover hit semantics and
restructures hover so interaction cost is independent of series length, without touching the backend
contract or introducing lossy down-sampling.

## What Changes

- Restructure the trend chart hover target from one `<rect onMouseEnter>` per point to a single
  transparent overlay `<rect>` covering the plot area with an `onMouseMove` handler that resolves the
  nearest data-point index. DOM node count for hover goes from O(n) to O(1).
- Change hover hit math from the band cell grid (`drawableWidth / n`) to the point grid
  (`drawableWidth / (n-1)`): resolve the index by `Math.round((pointerX - paddingLeft) / pointSpacing)`
  clamped to `[0, pointCount - 1]`, so the highlighted point is the one whose x-coordinate is nearest
  the cursor. Eliminates the half-band misalignment at series edges.
- Map screen pixels to viewBox units via `getBoundingClientRect` scaling
  (`clientX * viewBoxWidth / rect.width`), since the SVG renders through a `viewBox` with CSS scaling.
- Memoize series-derived values (`chartPoints`, `minPrice`/`maxPrice`, `linePath`) with `useMemo` keyed
  on `points`, and split hover-dependent subtrees (highlight `<circle>` + readout `<dl>`) so a hover
  index change re-renders O(1) nodes instead of re-running O(n) series computation.
- Rewrite the hover interaction test in `App.test.tsx`: the existing `getAllByTestId("trend-hover-band")`
  (asserting count 3) + `fireEvent.mouseEnter(band)` case no longer applies (one overlay node,
  `mouseMove`-driven). Extract the index-resolution as a pure `indexFromX(viewBoxX, pointCount)` helper
  and unit-test it directly, sidestepping jsdom's all-zero `getBoundingClientRect`.
- No backend, API contract, dependency, or database changes. Core-layer down-sampling (LTTB/stride)
  remains deferred -- now as a path-fidelity concern for very large series (>~10k points) rather than a
  hover-interaction blocker.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `etf-price-trend`: Tightens the trend chart hover requirement. "Indicates the nearest data point"
  becomes a precise contract -- hover resolves to the point whose x-coordinate is nearest the pointer
  (point-grid nearest, clamped to the series bounds), not the band cell currently under the pointer.
  This removes the half-band hit misalignment visible on short series. Interaction cost shall not scale
  with series length: hover resolution is a constant-time index computation and does not re-render the
  series-derived geometry per pointer move.

## Impact

- `apps/web/src/pages/EtfDetailPage.tsx`: `TrendChart` hover restructured -- single overlay rect,
  `onMouseMove` index resolution, `useMemo` for series geometry, hover-dependent subtree split; add
  `indexFromX` pure helper.
- `apps/web/src/App.test.tsx`: replace the per-band `mouseEnter` hover test with overlay `mouseMove`
  coverage plus direct `indexFromX` unit tests (including clamp and edge-alignment assertions).
- API / dependencies / database: none. The `GET /api/etfs/{etf_id}/prices` contract and the
  `etf-price-trend` endpoint/page/single-point/empty requirements are unchanged.
- Relationship to prior deferral: the original design (`add-etf-price-trend-chart` risk note) deferred
  down-sampling assuming interaction held below ~2000 points. By making hover O(1) in both DOM and
  re-render cost, this change raises the interaction-degradation threshold by an order of magnitude,
  so LTTB/stride down-sampling is no longer on the hover-critical path -- it remains available as a
  future path-fidelity optimization for exceptionally long series.

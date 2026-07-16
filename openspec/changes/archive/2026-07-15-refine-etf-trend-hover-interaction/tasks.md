## 1. Pure hover-index helper

- [x] 1.1 Add `indexFromX(viewBoxX, pointCount)` pure helper to `EtfDetailPage.tsx` (or a co-located util) using point-grid math `clamp(round((viewBoxX - paddingLeft) / (drawableWidth / (pointCount - 1))), 0, pointCount - 1)`, reading constants from `TREND_CHART`.
- [x] 1.2 Unit-test `indexFromX`: midpoint alignment (resolved index matches nearest point), left-edge clamp to 0, right-edge clamp to `pointCount - 1`, and the half-band-offset regression (cursor near a band boundary resolves to the nearest point, not the band cell).

## 2. TrendChart hover restructure

- [x] 2.1 Add `useMemo` for `chartPoints`, `minPrice`/`maxPrice`/`priceRange`, and `linePath`, keyed only on `points` (never `hoverIndex`).
- [x] 2.2 Replace the per-point `<rect onMouseEnter>` array with a single transparent overlay `<rect>` spanning the plot area (`paddingLeft..width-paddingRight`, `paddingTop..height-paddingBottom`) carrying `onMouseMove`.
- [x] 2.3 Implement the `onMouseMove` handler: convert `event.clientX` to viewBox units via `getBoundingClientRect` (`(clientX - rect.left) * TREND_CHART.width / rect.width`), call `indexFromX`, and `setHoverIndex` only when the resolved index differs from the current one.
- [x] 2.4 Keep `onMouseLeave` on the SVG clearing `hoverIndex` to null (readout falls back to the latest point).
- [x] 2.5 Split the hover-dependent nodes (highlight `<circle>` + readout `<dl>`) so a `hoverIndex` change re-renders only those, not the axis/grid/path subtrees.

## 3. Test migration

- [x] 3.1 Replace the `getAllByTestId("trend-hover-band")` (count 3) + `fireEvent.mouseEnter` case in `App.test.tsx` with an overlay `mouseMove` end-to-end test, mocking `getBoundingClientRect` to assert the readout and `trend-highlight` track the resolved point.
- [x] 3.2 Add an assertion that hover hit detection uses a single overlay element (one `trend-hover-overlay`, zero per-point hover bands) regardless of point count.
- [x] 3.3 Add a pointer-leave test asserting the readout reverts to the series' latest point.

## 4. Verification

- [x] 4.1 Run the web test suite (`vitest`) and confirm all trend-chart cases pass.
- [x] 4.2 Manually verify on a `Max` horizon for the oldest available ETF: a full cursor sweep stays responsive and the highlight tracks the pointer with no half-cell offset at both edges.

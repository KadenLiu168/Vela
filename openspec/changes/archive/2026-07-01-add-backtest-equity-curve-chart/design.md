## Context

The Backtest Detail page already loads persisted run metadata, metrics, parameters, and the full `equity_curve` array from `GET /api/backtests/{run_id}`. The frontend currently renders only text summaries and metric cards, while COP-112 asks for the first visual net value curve on this page.

## Goals / Non-Goals

**Goals:**

- Render a readable net value equity curve from `trade_date` and `net_value`.
- Handle empty curves and single-point curves as successful but limited data states.
- Keep the chart implementation small and local to the Backtest Detail page.
- Cover the behavior with frontend tests and OpenSpec requirements.

**Non-Goals:**

- Add drawdown curves, monthly returns, return distributions, holdings charts, or analytics beyond net value.
- Change backend routes, database models, or API response fields.
- Add a charting dependency.

## Decisions

1. Render the chart as inline SVG in `BacktestDetailPage.tsx`.
   - Rationale: COP-112 needs one simple line chart. SVG keeps the implementation dependency-free, testable in jsdom, and easy to style with the existing CSS.
   - Alternative considered: add a charting library. Rejected because it adds dependency and API surface for a first scoped line chart.

2. Treat only finite numeric `net_value` rows as chart points.
   - Rationale: the API type allows `net_value: string | null`; invalid or null values cannot be plotted safely. Filtering them keeps the chart stable while preserving the successful page state.
   - Alternative considered: plot nulls as zero. Rejected because that would invent data and distort the curve.

3. Use an empty state for zero valid points and a single-point state for one valid point.
   - Rationale: an SVG line needs at least two points. A single point is meaningful as a latest net value, but not a curve.
   - Alternative considered: draw a flat single-point line. Rejected because it implies a range that does not exist.

4. Keep date labels minimal: first and last trade date for multi-point curves, and trade date plus net value for single-point curves.
   - Rationale: this satisfies the acceptance criteria without building an axis system that belongs in a richer charting scope.

## Risks / Trade-offs

- Small SVG chart has limited axis detail -> Mitigation: show start/end date and min/max net value context.
- Large equity curves may create long SVG path strings -> Mitigation: acceptable for Phase 1 detail responses; pagination or downsampling is out of scope.
- Filtering invalid points can make a non-empty API curve render as empty -> Mitigation: empty copy says no valid net value points are available.

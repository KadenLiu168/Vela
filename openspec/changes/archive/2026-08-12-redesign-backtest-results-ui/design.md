## Context

Current Backtest Detail page renders the strategy's 11 `MetricCard`s, then each benchmark's 11+ `MetricCard`s as separate vertically-scrolling grids — there is no side-by-side strategy↔benchmark view. The equity-curve and rolling-stability charts (`equityCurveChart.ts` → `computeMultiEquityCurveGeometry`, hand-rolled SVG, no chart library) assign stroke color by **array position** (`0=acid-lime`, `1=teal`, `2+=violet`), use a **text-only `<ul>` legend with no swatch**, and draw **no axes/ticks**. The current backend contract produces exactly two fixed benchmarks, so the supported chart is strategy + `equal_weight_monthly` + `csi_300_buy_hold`; the defect is unstable identity when a series is absent, not an existing fourth-series collision. The Backtest List page table shows only Run / Date range / Status / Started at, although `BacktestListItem` already returns nullable `total_return`, `annualized_return`, `max_drawdown`, `volatility`, and `sharpe_ratio`. Design tokens live only in `apps/web/src/styles/tokens.css`. Constraint: `web-presentation-primitives` forbids introducing a generic chart framework, so charts stay hand-rolled SVG.

## Goals / Non-Goals

**Goals:**
- Side-by-side strategy↔benchmark **comparison matrix** on the Detail Overview (方案 A: keep each benchmark's absolute-metric rows *and* add relative rows).
- 4-card **hero** for the strategy headline metrics + **progressive disclosure** for secondary groups.
- Equity-curve and rolling-stability charts: **color-swatch legend** + readable **direct end-labels** + stable current-key→color mapping + **x/y axes**.
- Metric columns on the **Backtest List**.
- Six explicit **categorical palette** tokens in `tokens.css`, with three current identity roles and three reserved roles.
- Preserve nullable/legacy evidence, responsive local scrolling, keyboard access, and exact API-provided values.

**Non-Goals:**
- No backend / API / metric changes (all needed values are already returned).
- No charting-library introduction (keep hand-rolled SVG).
- No redesign of the Signals tab or other pages.
- No change to benchmark calculation semantics (`backtest-benchmark-comparison` untouched).

## Decisions

1. **One semantic table, not stacked cards or delta-chips.** Columns are Metric | Strategy | Equal-weight | CSI 300. The Absolute metrics row group contains values owned independently by each entity. The Strategy-relative row group leaves the Strategy cell `n/a` and places each strategy-versus-that-benchmark value in its benchmark column. *Alternative considered:* keep cards and append a delta chip — rejected because it still forces cross-section lookup.
2. **方案 A (absolute + relative row groups).** Retain each entity's absolute metrics and add strategy-relative Tracking Error, Information Ratio, Up/Down capture, and return-difference rows. Capture observation counts remain adjacent to their ratios. Longest-drawdown dates/recovery and other non-comparable evidence remain visible but are never ranked.
3. **Hero = 4 strategy-only cards** (Total return / CAGR (calendar-time) / Sharpe (daily returns, 252D) / Max drawdown). Benchmarks live in the matrix; the first screen answers "did my strategy work" before comparison detail. Matrix and list labels preserve the same annualization wording required by `web-frontend-app`.
4. **Only rank comparable absolute values.** Highlight Total return/CAGR/Sharpe/Sortino/Calmar by higher value; Max drawdown by the value closest to zero (numerically greatest); Volatility and longest drawdown duration by lower value. Exclude nulls, dates, relative rows, distribution statistics, and CAPM/capture evidence from ranking. Require at least two non-null comparable cells; mark every tied best cell and expose a textual/programmatic `Best` marker.
5. **Direct end-labels + swatch legend (dual signal).** Direct labels remove the legend↔line lookup; the text legend stays so identification is not color-only. Geometry returns endpoint coordinates, keeps labels inside the viewBox, and applies deterministic vertical separation for the supported three series. Exact values remain available in the existing summary/table fallback.
6. **Stable `seriesColor(key)` mapping for the current contract.** Explicitly map `strategy`, `equal_weight_monthly`, and `csi_300_buy_hold`; do not infer identity from array order. An unknown key uses a deterministic reserved-role fallback, but distinct unknown keys beyond remaining palette capacity are not promised collision-free. This keeps current identities consistent across detail and rolling-stability charts without pretending the API supports arbitrary benchmark counts.
7. **Declare exact categorical tokens in `tokens.css`.** Add `--color-series-1: var(--color-acid-lime)` (strategy), `--color-series-2: var(--color-signal-teal)` (equal weight), `--color-series-3: #4f8cff` (CSI 300), `--color-series-4: var(--color-coral-red)`, `--color-series-5: #f2b84b`, and `--color-series-6: #d96bd8` (reserved fallbacks). Update the leading catalog. Series 1–3 are consumed by both chart renderers; 4–6 are documented headroom. Colored direct-label text must meet WCAG AA normal-text contrast on `--surface-obsidian`.
8. **Axes in the shared hand-rolled geometry.** Extend `computeMultiEquityCurveGeometry` to return shared sorted-date x ticks, shared numeric y ticks, and endpoints derived from `EQUITY_CURVE_CHART`. Preserve the existing shared date/value scale and equal-range behavior. Equity and rolling charts format their own y-axis labels (net value, percent, or ratio) so differently scaled metrics are not mixed.
9. **Progressive disclosure via native `<details>`.** Distribution risk, return stability, and CSI-300 CAPM are three closed-by-default disclosures with accessible `<summary>` labels. Preserve owner identity, counts/status explanations, exact-value tables, and keyboard operation; collapsing changes visibility only, not evidence semantics.
10. **List columns from existing fields.** Add Total return / CAGR (calendar-time) / Sharpe (daily returns, 252D) to `BacktestListPage` using already-returned nullable `BacktestListItem` fields and existing formatters — zero API change.
11. **Responsive dense-data containment.** The comparison matrix and expanded list table use labeled, keyboard-scrollable local overflow regions; the metric-name column is sticky. At 1440×1000 and 390×844 there is no page-level horizontal overflow, and chart labels/ticks remain inside their SVG viewBoxes.

## Risks / Trade-offs

- **[Matrix width on narrow screens]** → place the table in a labeled local horizontal-scroll region and keep the metric-name column sticky; do not allow page-level overflow.
- **[Direct labels overlap when lines converge]** → use deterministic vertical separation for the supported strategy + two benchmarks, clamp labels inside the viewBox, and retain the text/swatch legend plus exact-value fallback.
- **[Token edits need design-system control]** → all additions live in `tokens.css` with the catalog comment block updated.
- **[Reserved palette colors are not current benchmark support]** → test collision-free identity only for the three currently supported keys and document fallback capacity rather than changing backend semantics.
- **[Regression in chart geometry and fallback states]** → keep `EQUITY_CURVE_CHART` as the geometry source of truth and explicitly test empty, one-point, equal-range, missing-series, endpoint separation, ticks, and viewBox bounds.

## Migration Plan

Frontend-only; no DB or migration. Rollback = revert the scoped frontend and OpenSpec changes. Before merge, run focused component/geometry tests; deterministic browser acceptance at 1440×1000 and 390×844; the complete web gate (`npm --prefix apps/web run lint`, `lint:css`, `typecheck`, `test`, `build`); then `npm --prefix apps/web run check:bundle` against that fresh build.

## Open Questions

- None. Palette size is six, list sorting is deferred, and CAPM remains gated to `csi_300_buy_hold`.

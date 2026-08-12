## Why

Users reviewing backtest results hit two UX problems. (1) The Backtest Detail page stacks the strategy's 11 MetricCards and then each benchmark's 11+ MetricCards as separate vertically-scrolling grids with **no side-by-side comparison**, so judging how the strategy performs against benchmarks requires mental arithmetic. (2) The equity-curve and rolling-stability charts assign colors by array position, use a **text-only legend with no color swatch**, and draw **no axes/ticks**, so a series identity can change when another series is absent and values are hard to read. The Backtest List page also ignores the metric fields the API already returns, offering no at-a-glance screening.

## What Changes

- Add a side-by-side **strategy ↔ benchmark comparison matrix** on the Detail Overview (方案 A: keep each benchmark's absolute-metric rows *and* add relative rows — Tracking Error, Information Ratio, Up / Down capture, return differences).
- Collapse the 11+11+… MetricCard grids into a 4-card **hero** (strategy Total return / CAGR (calendar-time) / Sharpe (daily returns, 252D) / Max drawdown) plus the comparison matrix; move VaR / CVaR / skew / kurtosis, rolling stability, and CAPM into **collapsible** sections (progressive disclosure).
- Redesign the equity-curve chart: legend gains **color swatches**; each line gets a readable **direct end-label**; the strategy and the two fixed benchmark keys bind to stable categorical colors; add **x (date) and y (net-value) axes / ticks** while preserving empty and single-point fallbacks.
- Extend the design-system color tokens with a six-color categorical palette: three stable roles cover the current strategy + exactly two fixed benchmarks and three are documented headroom. Apply the same chart treatment to Return Stability rolling charts through the shared geometry module.
- Add metric columns (Total return, CAGR (calendar-time), Sharpe (daily returns, 252D)) to the **Backtest List** table using the already-returned `BacktestListItem` fields.

## Capabilities

### New Capabilities
- `backtest-results-ui`: Redesigned presentation layer for backtest results — detail-page hero metrics, side-by-side strategy↔benchmark comparison matrix (absolute + relative row groups), progressive disclosure of secondary metric groups without hiding evidence, equity/rolling chart legend / direct-labels / stable-colors / axes, list-page metric columns, and responsive/accessibility behavior.

### Modified Capabilities
- `design-system`: Add six named categorical series tokens, pin the current strategy and two fixed benchmark keys to stable roles, and reserve three roles as future headroom.

## Impact

- **Frontend**: `apps/web/src/pages/BacktestDetailPage.tsx`, `BacktestListPage.tsx`, `equityCurveChart.ts`, `ReturnStabilitySection.tsx`, `DistributionRiskSection.tsx`, `styles.css`; new/updated `apps/web/src/styles/tokens.css` categorical color tokens; likely a new `seriesColor(key)` helper.
- **No backend / API changes** — every metric and evidence count the matrix/disclosures need (total return, CAGR, MaxDD, Vol, Sharpe, Sortino, Calmar, longest-drawdown fields, tracking error, information ratio, up/down capture and counts, CAPM and count, return differences, distribution evidence) is already returned by `getBacktestDetail`; list columns use existing nullable `BacktestListItem` fields.
- **Design-token change-control**: per `design-system`, all token edits MUST live only in `tokens.css` and the catalog comment block must list the new group.

## 1. Characterize Presentation Contracts

- [x] 1.1 Add a focused `DescriptionItem` component test that requires sibling `<dt>/<dd>` output, no layout wrapper, and a linked React value.
- [x] 1.2 Add failing direct tests for Dashboard and Backtest domain formatter outputs, including empty symbols, valid/malformed/null parameter JSON, and equity-point readouts.
- [x] 1.3 Add failing direct Equity Curve geometry tests for invalid-point filtering, two-point and multi-point paths, plot bounds, equal values, extrema ties, and duplicate highlights.
- [x] 1.4 Add dedicated ETF Trend geometry tests for index clamping, date-axis selection, normal ranges, equal values, and path bounds before moving existing pure assertions out of `App.test.tsx`.

## 2. Canonical Description Item

- [x] 2.1 Implement `components/DescriptionItem.tsx` with a string label, `ReactNode` value, and wrapper-free `<dt>/<dd>` rendering, then expose it through the existing component export convention.
- [x] 2.2 Replace every local `Detail` use in Dashboard, ETF Detail, Signal Detail, and Backtest Detail with `DescriptionItem`, including the linked Backtest value in Signal Detail.
- [x] 2.3 Remove only the four obsolete local `Detail` definitions and verify that `Metric`, `MetricCard`, and `StatusPillBadge` remain unchanged and local.

## 3. Page-Domain Formatters

- [x] 3.1 Create a React-free `pages/dashboardFormatters.ts` for momentum windows, score weights, defensive assets, and failed symbols using scalar or small structural inputs.
- [x] 3.2 Switch Dashboard call sites to the domain formatter module and remove only the superseded local formatter functions.
- [x] 3.3 Create a React-free `pages/backtestFormatters.ts` for parameter summaries and composite equity-point readouts.
- [x] 3.4 Switch Backtest Detail call sites to the domain formatter module and remove only the superseded local formatter functions.
- [x] 3.5 Run the formatter and page tests to verify punctuation, fallbacks, rendered copy, and component-only page exports remain unchanged.

## 4. Framework-Independent Chart Geometry

- [x] 4.1 Create `pages/equityCurveChart.ts` with `EQUITY_CURVE_CHART`, chart types, valid-point normalization, multi-point coordinates/path computation, extrema values, and deterministic latest/min/max highlight selection.
- [x] 4.2 Update `BacktestDetailPage.tsx` to consume the extracted geometry and derive SVG viewBox and grid-line bounds from `EQUITY_CURVE_CHART`.
- [x] 4.3 Remove the obsolete page-local Equity Curve types and geometry helpers, keeping empty and single-point rendering in the page component.
- [x] 4.4 Move direct `indexFromX` assertions from `App.test.tsx` into `etfTrendChart.test.ts` after the dedicated tests pass, while retaining ETF hover and chart-state integration tests.
- [x] 4.5 Run both dedicated chart test files and the Backtest/ETF page tests to verify equal-value, extrema, empty, single-point, multi-point, and hover behavior.

## 5. Quality Gates

- [x] 5.1 Run the complete web Vitest suite and confirm all tests pass.
- [x] 5.2 Run TypeScript type checking and ESLint, confirming page modules remain compatible with React Fast Refresh.
- [x] 5.3 Run Stylelint and the CSS root/token check, confirming the refactor does not alter CSS contracts.
- [x] 5.4 Run the production web build and inspect the final diff to confirm no API, route, dependency, token, copy, or visual-contract changes entered scope.

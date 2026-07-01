## 1. Frontend Coverage

- [x] 1.1 Add Backtest Detail page tests for a multi-point equity curve rendered from API data.
- [x] 1.2 Add Backtest Detail page tests for empty and single-point equity curve states.
- [x] 1.3 Add a regression assertion that the page does not render drawdown, monthly returns, or return distribution charts.

## 2. Frontend Implementation

- [x] 2.1 Render an equity curve section on `BacktestDetailPage` from `equity_curve[].trade_date` and `equity_curve[].net_value`.
- [x] 2.2 Draw a dependency-free SVG line chart for two or more valid net value points.
- [x] 2.3 Render stable empty and single-point states without treating successful detail responses as errors.
- [x] 2.4 Add scoped CSS for the equity curve section and responsive chart layout.

## 3. Validation

- [x] 3.1 Run focused frontend tests for Backtest Detail behavior.
- [x] 3.2 Run frontend lint, typecheck, build, and full frontend test suite.
- [x] 3.3 Run repository Python tests, Ruff, and OpenSpec validation.

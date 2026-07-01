## Why

Backtest Detail already loads persisted run details and metrics, but it does not visualize the returned equity curve. COP-112 needs the first front-end chart on that page so users can inspect the run's net value path from real `BacktestEquityCurve` response data.

## What Changes

- Render an equity curve section on the Backtest Detail page using `equity_curve[].trade_date` and `equity_curve[].net_value` from `GET /api/backtests/{run_id}`.
- Show a simple line chart for two or more valid curve points.
- Show reasonable empty and single-point states without treating successful API responses as failures.
- Keep this change scoped to net value only; do not add drawdown curves, monthly returns, return distributions, backend routes, or new dependencies.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Backtest Detail gains a net value equity curve display sourced from the existing detail API response.

## Impact

- Affects `apps/web/src/pages/BacktestDetailPage.tsx`, `apps/web/src/styles.css`, and related frontend tests.
- Updates `openspec/specs/web-frontend-app/spec.md` through a delta spec.
- Reuses the existing `GET /api/backtests/{run_id}` response shape and shared API client types.
- Adds no new runtime dependencies.

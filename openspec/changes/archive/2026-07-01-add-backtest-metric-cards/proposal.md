## Why

COP-111 needs the Backtest Detail page to make core performance metrics immediately scannable. The detail page already loads the real backtest detail API, but the metrics are rendered as a plain definition list and nullable values are not shown with the requested `n/a` state.

## What Changes

- Render total return, annualized return, maximum drawdown, volatility, and Sharpe ratio as metric cards on the Backtest Detail page.
- Keep all metric values sourced from the existing `GET /api/backtests/{run_id}` detail response.
- Show nullable metric values as `n/a`.
- Format percentage metrics clearly as percentages and Sharpe ratio clearly as a decimal value.
- Add focused frontend test coverage for populated and nullable metric card states.
- Do not change backend APIs, database models, equity curve rendering, or dashboard behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Backtest Detail renders API-backed core metrics as readable metric cards with clear null and numeric formatting.

## Impact

- Affects `apps/web/src/pages/BacktestDetailPage.tsx`, `apps/web/src/styles.css`, and related frontend tests.
- Updates the `web-frontend-app` OpenSpec capability.
- Reuses the existing `GET /api/backtests/{run_id}` response shape without changing backend code or shared API helper contracts.

## Why

The Backtest Detail page already shows the equity curve chart, but users still need a compact way to verify the returned curve data before deeper analysis exists. COP-113 requires a first-pass summary from the real backtest detail API so users can confirm point count and boundary values.

## What Changes

- Add a basic equity curve summary to the Backtest Detail page.
- Show the count of valid equity curve points used by the page.
- Show first and last valid curve points with trade date and net value.
- Keep the existing minimum and maximum net value summary.
- Keep the scope limited to a simple summary; do not add a full analysis dashboard.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Extend Backtest Detail equity curve behavior with a basic summary sourced from `GET /api/backtests/{run_id}`.

## Impact

- Frontend Backtest Detail rendering in `apps/web/src/pages/BacktestDetailPage.tsx`.
- Frontend route tests in `apps/web/src/App.test.tsx`.
- OpenSpec `web-frontend-app` requirements.
- No backend API, database schema, or dependency changes.

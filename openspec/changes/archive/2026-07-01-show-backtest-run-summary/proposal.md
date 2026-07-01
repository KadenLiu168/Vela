## Why

After a backtest is submitted from the Dashboard, the frontend currently only confirms that the request was submitted. Users need the returned run summary immediately so they can verify the real API result and continue into the backtest detail workflow.

## What Changes

- Show a Dashboard operation summary after `POST /api/backtests/run` succeeds.
- Include the returned run id, status, trading day count, signal count, and core metric summary.
- Provide a link from the successful run summary to the corresponding Backtest Detail route.
- Keep failed backtest requests as operation-level error summaries.
- Do not change the run backtest API request or response contract.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Dashboard backtest submission must render the real run API response summary and detail entry point.

## Impact

- Affects `apps/web/src/pages/DashboardPage.tsx` and related frontend tests.
- Updates the `web-frontend-app` OpenSpec capability.
- No backend API, database, dependency, or routing contract changes are expected.

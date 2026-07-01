## Why

The Dashboard currently exposes `Run backtest` only as a disabled placeholder, so users cannot run a historical backtest from the web workflow. COP-107 requires the first interactive Dashboard backtest action using the existing real run-backtest API.

## What Changes

- Add start date and end date inputs to the Dashboard operations area using the existing visual system.
- Validate required `YYYY-MM-DD` dates and ensure `startDate <= endDate` before submitting.
- Submit valid runs through the shared frontend API client to `POST /api/backtests/run?startDate=...&endDate=...`.
- Show only scoped submission status for successful submit and existing operation-level failure copy.
- Do not add a backtest detail entry point, post-run recent-backtest refresh, or richer result summary.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Dashboard users can input a backtest date range, submit it to the real run-backtest API, and receive scoped validation/operation feedback.

## Impact

- `apps/web/src/pages/DashboardPage.tsx`
- `apps/web/src/api/client.ts`
- Frontend unit/integration tests under `apps/web/src`
- `openspec/specs/web-frontend-app/spec.md` after archive

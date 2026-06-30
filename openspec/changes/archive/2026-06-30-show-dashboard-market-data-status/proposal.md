## Why

Dashboard users need to know whether local market data exists before generating signals or backtests. COP-87 renders the aggregate Dashboard, but empty market data still appears only as zero metrics and unavailable dates, which is not explicit enough to guide the next action.

## What Changes

- Make the Dashboard market data panel explicitly show local market data status from `GET /api/dashboard`.
- Show earliest trade date, latest trade date, price record count, and ETF coverage when market prices exist.
- Show a clear empty state when the dashboard aggregate reports no market price rows.
- Add focused frontend coverage for the empty market data state while retaining real dashboard API and SQLite validation through existing API tests.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Dashboard market data status must explicitly represent populated and empty local market data states from the dashboard aggregate.

## Impact

- Affected frontend files: `apps/web/src/pages/DashboardPage.tsx`, `apps/web/src/App.test.tsx`, and possibly `apps/web/src/styles.css`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` via this change's delta spec.
- No API contract change is expected; the existing `GET /api/dashboard` response already includes the required market data fields.

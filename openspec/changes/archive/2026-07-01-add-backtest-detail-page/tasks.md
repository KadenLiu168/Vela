## 1. API Client

- [x] 1.1 Add typed backtest detail response shapes to the shared frontend API client.
- [x] 1.2 Add a `getBacktestDetail` helper that calls `GET /api/backtests/{run_id}`.
- [x] 1.3 Add API client unit coverage for the backtest detail helper.

## 2. Backtest Detail Page

- [x] 2.1 Replace the placeholder page with API-backed loading, ready, missing-run, and API failure states.
- [x] 2.2 Render run metadata, date range, status, timestamps, error state, metrics, and parameter summary from the API response.
- [x] 2.3 Keep the page scoped to core detail fields without adding equity curve charts or backend changes.

## 3. Validation

- [x] 3.1 Add page tests for successful detail rendering, loading state, missing-run state, and generic API failure state.
- [x] 3.2 Run focused frontend tests for the API client and Backtest Detail page.
- [x] 3.3 Run available frontend validation and OpenSpec validation commands.

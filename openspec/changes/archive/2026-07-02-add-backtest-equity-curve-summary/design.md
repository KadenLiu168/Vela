## Context

The Backtest Detail page already loads `GET /api/backtests/{run_id}` through the shared frontend API client and renders an equity curve chart from valid `net_value` rows. The current chart summary shows dates and min/max net values, but it does not explicitly show the valid point count or the first and last net values together.

## Goals / Non-Goals

**Goals:**

- Add a compact summary that helps users verify the returned equity curve.
- Use only the valid equity curve points already derived from the real API response.
- Keep the first version simple and readable.

**Non-Goals:**

- Do not add backend fields or change the API response contract.
- Do not add a full analysis dashboard, drawdown table, monthly returns table, or pagination.
- Do not change the chart rendering model beyond the summary copy.

## Decisions

- Reuse the existing `getValidEquityCurvePoints` output for summaries so chart and summary values are based on the same filtered data.
- Show point count, start date/net value, end date/net value, minimum net value, and maximum net value in the existing summary list.
- Keep the empty and single-point states focused on the same summary concepts instead of introducing a separate table component.

## Risks / Trade-offs

- Summary values ignore invalid or null `net_value` rows because the chart also ignores them. This keeps user-visible values consistent with the plotted curve.
- A compact summary is less detailed than a full table, but it satisfies COP-113 without expanding into a larger analytics surface.

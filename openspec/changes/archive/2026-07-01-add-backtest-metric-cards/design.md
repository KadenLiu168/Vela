## Context

`BacktestDetailPage` already fetches `GET /api/backtests/{run_id}` through the shared frontend API client and receives a `metrics` object with total return, annualized return, maximum drawdown, volatility, and Sharpe ratio. The current page renders those values inside a compact definition list, which satisfies data presence but does not provide the metric-card presentation or `n/a` null state required by COP-111.

## Goals / Non-Goals

**Goals:**

- Present the five core performance metrics as cards in the Backtest Detail page.
- Use only values from the existing detail API response.
- Format return, drawdown, and volatility values as percentages.
- Format Sharpe ratio as a decimal value.
- Render nullable metric values as `n/a`.
- Keep the implementation small and local to the existing detail page.

**Non-Goals:**

- Add or change backend endpoints, database fields, or API client response types.
- Add equity curve charts, holdings tables, trend indicators, or comparisons.
- Change Dashboard metric summaries.
- Introduce new dependencies or shared component abstractions.

## Decisions

1. Reuse the existing detail response and page state.
   - Rationale: COP-110 already connected the route to the real API and the backend spec confirms the required metric fields.
   - Alternative considered: add another API helper or transform layer. Rejected because it would duplicate the existing contract without adding value.

2. Keep metric cards as a local rendering helper in `BacktestDetailPage`.
   - Rationale: only one page needs this card layout today, so a shared component would add abstraction before reuse exists.
   - Alternative considered: create a reusable `MetricCard` component under `components/`. Rejected for current scope.

3. Use `n/a` for metric nulls and preserve existing `Not available` copy for non-metric metadata.
   - Rationale: COP-111 explicitly scopes `n/a` to nullable metrics, while COP-110 metadata states already use `Not available`.
   - Alternative considered: change every nullable field to `n/a`. Rejected as unrelated behavior.

## Risks / Trade-offs

- Percentage fields arrive as decimal strings, so invalid strings could bypass formatting. Mitigation: keep the existing fallback of displaying the raw value if parsing fails.
- Card layout adds CSS specific to detail metrics. Mitigation: keep class names scoped to backtest metric cards and reuse existing color/spacing conventions.

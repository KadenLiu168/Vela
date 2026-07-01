## Context

The Dashboard Operations panel already contains a date-range form that calls the shared `runBacktest()` API helper. The API response includes the fields required for a run summary, but the page currently discards the response and only renders a generic submitted message.

## Goals / Non-Goals

**Goals:**

- Preserve the existing Dashboard backtest form and shared API client call.
- Store the successful `BacktestRunResponse` in Dashboard state.
- Render run id, status, trading day count, signal count, total return, annualized return, maximum drawdown, volatility, and Sharpe ratio.
- Provide a local client-side link to `/backtests/<run_id>` after a successful run.
- Keep failed requests in the existing operation-level error path.

**Non-Goals:**

- Do not change the FastAPI backtest run endpoint or response schema.
- Do not implement the full Backtest Detail page.
- Do not add polling, background job state, or async run tracking.

## Decisions

- Reuse `BacktestRunResponse` from `apps/web/src/api/client.ts` in Dashboard state rather than introducing a new local DTO.
- Replace the boolean submitted flag with response state so the UI can render the actual API result.
- Use a regular app link to `/backtests/${run_id}` because the app already handles client-side navigation through `AppShell`.
- Leave HTTP and network failures as normalized `operationError` messages because that is the existing operation pattern.

## Risks / Trade-offs

- Backtest Detail is still placeholder-level, so the entry point is useful for route continuity but not a full analytical view yet. This is acceptable because COP-108 only requires the success entry point.
- The successful run summary reflects the immediate API response and does not poll for later updates. This matches the current synchronous `POST /api/backtests/run` behavior.

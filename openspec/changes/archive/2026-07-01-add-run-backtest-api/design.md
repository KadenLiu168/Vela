## Context

The API service already exposes thin command endpoints for market data fetching and strategy signal generation. Those endpoints use request-scoped SQLite sessions, call existing `vela_core` workflows, and return compact JSON summaries. The core `run_backtest` function already accepts a SQLAlchemy session, strategy config, start date, and end date, and persists `BacktestRun` plus `BacktestEquityCurve` rows.

## Goals / Non-Goals

**Goals:**
- Expose a minimal local HTTP endpoint that frontend code can call to run a backtest for a requested date range.
- Reuse the existing core `run_backtest` behavior and API database session dependency.
- Return the run id, status, date range, trading day count, signal count, and core metrics from the core result.
- Validate the endpoint through a real FastAPI request and temporary SQLite database.

**Non-Goals:**
- Do not add backtest list/detail endpoints.
- Do not add frontend wiring.
- Do not add new persistence tables or duplicate backtest calculations in the API layer.
- Do not introduce async/background execution.

## Decisions

1. Add `POST /api/backtests/run?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD`.
   - Rationale: Existing command endpoints use POST plus query parameters, including camelCase API parameters such as `signalDate`.
   - Alternative considered: JSON request body. That would be reasonable for a larger command payload, but COP-104 only needs two dates and the existing API style is query-based.

2. Keep the API layer as a thin wrapper over `vela_core.run_backtest`.
   - Rationale: Core already owns signal generation, equity curve calculation, metrics, and persistence.
   - Alternative considered: Add an API-specific service wrapper. That would add indirection without removing meaningful duplication for this single endpoint.

3. Map expected `ValueError` failures to HTTP 400.
   - Rationale: `run_backtest` already raises `ValueError` for invalid date range and missing local market prices; those are client/request precondition failures.
   - Alternative considered: Let exceptions bubble as 500. That would make normal validation failures look like server errors.

## Risks / Trade-offs

- Long-running requests can block until the backtest completes -> keep COP-104 synchronous because existing local workflows are synchronous and no background job system exists yet.
- Response metrics are serialized as strings for decimals -> this matches existing API decimal response helpers and avoids float rounding.

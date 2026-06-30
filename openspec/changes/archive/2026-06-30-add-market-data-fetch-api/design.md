## Context

The API service already exposes read endpoints and uses a request-scoped SQLAlchemy session dependency. Core market data workflows already provide `fetch_incremental_market_prices` and `fetch_full_market_prices`, and their result object contains the counts and error details COP-93 requires.

## Goals / Non-Goals

**Goals:**

- Expose a frontend-callable market data fetch API for `incremental` and `full` modes.
- Keep fetch workflow behavior inside `vela_core`.
- Return the existing core workflow result fields in an HTTP-friendly JSON shape.
- Validate the route through FastAPI, temporary SQLite, and a controlled provider.

**Non-Goals:**

- Do not add scheduling, background jobs, cancellation, or progress streaming.
- Do not change full or incremental fetch semantics.
- Do not add frontend UI for triggering the endpoint.

## Decisions

1. Use `POST /api/market-data/fetch?mode=incremental|full`.

   Rationale: fetching market data mutates SQLite and writes fetch logs, so `POST` better reflects the command behavior than `GET`. The query parameter matches the issue's `mode=incremental|full` wording and avoids introducing a request body for a single option.

   Alternative considered: `GET /api/market-data/fetch`. Rejected because the endpoint has side effects.

2. Use a provider dependency.

   Rationale: production requests can use `AkShareMarketDataProvider`, while tests can override the dependency with a controlled provider without mocking the core workflow. This follows FastAPI's existing dependency style and keeps external network calls out of integration tests.

   Alternative considered: instantiate the provider inline in the route. Rejected because it would make SQLite integration validation require real network data or brittle monkeypatching.

3. Return the existing `MarketDataFetchResult` fields directly.

   Rationale: the core result already includes status, requested symbol count, row counts, failed symbols, and error message. Keeping the API response as a serialization of that object avoids duplicating market data accounting in the API layer.

   Alternative considered: query `DataFetchLog` after the workflow completes. Rejected because it would miss `failed_symbols`, add another persistence read, and duplicate data already returned by the workflow.

## Risks / Trade-offs

- Long-running provider calls can block an HTTP request -> Mitigation: keep this first version synchronous because COP-93 only asks for a callable API, and defer background execution to a separate issue.
- Production provider depends on external AkShare availability -> Mitigation: integration tests use a controlled provider with real SQLite persistence to verify API behavior without external network dependence.
- Incremental mode fails without a local baseline by existing core design -> Mitigation: return the core `failed` status and error message unchanged so the frontend can display the condition.

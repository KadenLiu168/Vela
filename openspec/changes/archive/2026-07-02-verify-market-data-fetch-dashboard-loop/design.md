## Context

The API already exposes `POST /api/market-data/fetch` and `GET /api/dashboard`. The web Dashboard already calls the shared market data fetch client and reloads the Dashboard aggregate after a successful fetch. Existing tests validate those pieces separately, but COP-124 needs a single closed-loop validation from fetch command to persisted rows to refreshed Dashboard state.

## Goals / Non-Goals

**Goals:**
- Validate the market data fetch and Dashboard refresh source against the same temporary SQLite database.
- Exercise the real FastAPI endpoints, request-scoped database session, and existing core market data fetch workflow.
- Verify both persisted `MarketPrice`/`DataFetchLog` rows and the follow-up Dashboard API response.

**Non-Goals:**
- Do not change production API or frontend behavior.
- Do not call the live AkShare provider in automated tests.
- Do not cover signal generation, backtest execution, or the full P0 user flow in this COP.

## Decisions

- Use a pytest API integration test with `TestClient`, a temporary SQLite database, and `ControlledMarketDataProvider`.
  - This covers real API routing, dependency overrides, session wiring, core workflow persistence, and Dashboard aggregation without network flakiness.
  - Browser-level E2E would be broader than COP-124 and would duplicate existing frontend click/refresh tests.
- Add the closed-loop test beside existing market data fetch API tests.
  - The endpoint setup and provider override patterns already live there, so the change remains localized.

## Risks / Trade-offs

- Controlled provider does not prove live data source availability -> Existing provider-specific tests and manual validation remain responsible for live-source behavior.
- API-level test does not render the browser Dashboard -> Existing frontend tests already verify that the Dashboard sends the fetch request and renders the refreshed Dashboard response.

## Context

The API already exposes `POST /api/market-data/fetch?mode=full` and `mode=incremental`, and the Dashboard already calls the incremental endpoint through the shared frontend API client. The Dashboard also has an operation summary component that renders the shared market data fetch response shape.

COP-96 is therefore a frontend entry-point change: expose full fetch without making it the primary market data action.

## Goals / Non-Goals

**Goals:**

- Let the Dashboard trigger the existing full market data fetch API.
- Keep incremental fetch visually and behaviorally ahead of full fetch.
- Reuse the existing market data fetch summary for full fetch results.
- Validate the full fetch helper against the local API response contract backed by SQLite.

**Non-Goals:**

- Do not change backend market data fetch semantics.
- Do not add scheduling, confirmation dialogs, cancellation, or progress streaming.
- Do not change the fetch response shape or Dashboard aggregate API.

## Decisions

1. Add a separate `fetchFullMarketData` helper beside `fetchIncrementalMarketData`.

   Rationale: the backend API already models fetch mode as a query parameter, and explicit helpers keep page code readable. An alternative generic `fetchMarketData(mode)` would be slightly less code, but the current client uses endpoint-specific helpers and only needs two modes.

2. Keep one pending state for both market data fetch actions.

   Rationale: full and incremental fetches write the same local tables and should not run concurrently from the Dashboard. A single state matches the existing duplicate-submission guard.

3. Render full fetch as a secondary operation after incremental fetch.

   Rationale: incremental fetch remains the normal low-cost action. Full fetch is available for initialization or repair, but its label and placement communicate lower priority. A separate panel or modal would add UI complexity without changing behavior.

4. Reuse `MarketDataFetchSummary` unchanged.

   Rationale: both API modes return the same summary contract. The summary can remain mode-agnostic because COP-96 only requires result reuse, not mode-specific reporting.

## Risks / Trade-offs

- Users may still trigger a long full fetch accidentally -> Mitigation: place full fetch after incremental fetch and label it as a full initialization/repair action.
- A single loading label cannot distinguish which mode is currently running -> Mitigation: use mode-specific button labels while preserving one concurrency guard.
- Real API integration depends on a running local FastAPI service with SQLite test setup -> Mitigation: keep the existing opt-in `VITE_API_BASE_URL` integration test pattern and add full fetch coverage there.

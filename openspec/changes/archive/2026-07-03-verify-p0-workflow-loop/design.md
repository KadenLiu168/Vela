## Context

COP-124, COP-125, and COP-126 validate the market data, signal generation, and backtest loops individually. COP-127 needs one end-to-end P0 workflow validation that uses the same local API app and SQLite database across all steps and verifies that refresh-style reads recover persisted backend state.

## Goals / Non-Goals

**Goals:**
- Validate the P0 workflow through real FastAPI endpoints and existing backend workflows.
- Confirm persisted state is readable after operations through Dashboard, latest signal, and backtest detail endpoints.
- Let users open Signal Detail and Backtest Detail from persisted Dashboard summaries after refresh.
- Record backend/API gaps found during the workflow validation.

**Non-Goals:**
- Do not add browser E2E infrastructure.
- Do not change production API, strategy logic, or backtest logic.
- Do not clean unrelated spec contradictions in this change.

## Decisions

- Use one pytest API integration test with `TestClient`, a temporary SQLite database, and `ControlledMarketDataProvider`.
  - This covers the real API and backend workflow sequence without requiring a dev server or browser automation.
  - Existing frontend tests already cover Dashboard controls, operation summaries, refresh behavior, and detail rendering from API-shaped responses.
- Seed deterministic market history through the day before the fetch, then let the fetch endpoint add the latest day.
  - This keeps the workflow independent from live provider/network availability while still using the real fetch workflow and persistence.
- Add detail links to populated Dashboard summary components.
  - Latest signal links to the existing Signal Detail route, which is currently backed by the latest signal API.
  - Recent backtest links to `/backtests/<run_id>`, matching the generated operation result link and the existing Backtest Detail route.

## Risks / Trade-offs

- API-level validation does not literally click in the browser -> Existing frontend tests cover the UI layer; this change validates the backend capabilities behind those UI calls.
- A live API-backed frontend integration remains manual/service-dependent -> Keep it outside this COP to avoid fragile local orchestration.
- Backend/API gap record: no blocking backend gaps or response-field mismatches were found for the tested P0 workflow. Signal Detail still reads the latest signal rather than a signal-id-specific endpoint; that matches the current API surface and should be handled separately if signal-id detail becomes required.

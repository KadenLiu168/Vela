## Context

The API already exposes `POST /api/strategy-signals/generate`, `GET /api/strategy-signals/latest`, and `GET /api/dashboard`. The web Dashboard already triggers signal generation and refreshes persisted latest signal data, while the Signal Detail page reads the latest signal endpoint. Existing tests validate these pieces separately.

## Goals / Non-Goals

**Goals:**
- Validate signal generation, persistence, latest signal reads, and Dashboard latest signal reads against the same temporary SQLite database.
- Exercise the real FastAPI endpoints, request-scoped database session, and existing core signal generation workflow.
- Confirm Dashboard and Signal Detail data sources identify the same persisted signal after generation.

**Non-Goals:**
- Do not change production API, frontend UI, or signal generation logic.
- Do not introduce browser E2E infrastructure.
- Do not validate backtest execution or the complete P0 user flow in this COP.

## Decisions

- Use a pytest API integration test with `TestClient` and deterministic SQLite seed data.
  - This covers real API routing, session lifecycle, signal generation, persistence, latest signal reporting, and Dashboard aggregation without adding UI test infrastructure.
  - Existing React tests already verify that Dashboard and Signal Detail render the shared API responses consistently.
- Add the closed-loop test beside existing signal generation API tests.
  - The setup for enough market price history already exists there, so the change stays localized.

## Risks / Trade-offs

- API-level validation does not click the browser UI -> Existing frontend tests continue to cover the click, refresh, and rendering behavior from API-shaped responses.
- Deterministic seed data may not cover all strategy edge cases -> COP-125 only requires the first successful closed loop, not exhaustive strategy validation.

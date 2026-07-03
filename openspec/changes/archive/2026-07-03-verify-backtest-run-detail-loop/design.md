## Context

The API already exposes `POST /api/backtests/run` and `GET /api/backtests/{run_id}`. The backtest workflow generates historical signals, calculates equity curve rows, and persists the run result. The web Dashboard already submits date ranges and links to the Backtest Detail page, while Backtest Detail renders metrics and equity curve rows from the detail API.

## Goals / Non-Goals

**Goals:**
- Validate backtest execution, persistence, and detail API reads against the same temporary SQLite database.
- Exercise the real FastAPI endpoints, request-scoped database session, existing backtest workflow, and persisted detail read path.
- Confirm the detail API returns metric and equity curve data for the generated run id.

**Non-Goals:**
- Do not change production API, frontend UI, or backtest calculation logic.
- Do not introduce browser E2E infrastructure.
- Do not validate the full P0 user journey in this COP.

## Decisions

- Use a pytest API integration test with `TestClient` and deterministic local market price history.
  - This covers the backend workflow and persisted read path without adding slow browser orchestration.
  - Existing React tests already validate Dashboard submission and Backtest Detail rendering from API-shaped responses.
- Add the closed-loop test beside existing backtest API tests.
  - The file already contains helpers for seeding enough price history for a successful run.

## Risks / Trade-offs

- API-level validation does not render the browser chart -> Existing frontend tests continue to cover metric cards and equity curve rendering.
- The deterministic price fixture validates the closed loop, not every backtest calculation edge case -> Existing core tests remain responsible for calculation coverage.

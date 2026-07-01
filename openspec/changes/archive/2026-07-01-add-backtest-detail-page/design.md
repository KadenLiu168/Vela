## Context

The web app already has client-side routing for `/backtests/:id`, but `BacktestDetailPage` only renders placeholder text. The API already exposes `GET /api/backtests/{run_id}` and returns persisted run metadata, metrics, and equity curve rows with a stable 404 response for missing runs.

## Goals / Non-Goals

**Goals:**

- Load a single backtest run by route id through the shared frontend API client.
- Render core run metadata: run id, strategy name, config version, date range, status, timestamps, error message, metrics, and parameter summary.
- Provide stable loading, not-found, and generic API failure states.
- Cover the API helper and page behavior with focused frontend tests.

**Non-Goals:**

- Do not add or change backend endpoints.
- Do not render equity curve charts, holdings tables, or advanced analytics.
- Do not add a backtest list page or dashboard behavior.
- Do not introduce new dependencies or routing libraries.

## Decisions

1. Reuse the existing route id as the API path parameter.
   - Rationale: the current router already extracts `/backtests/:id`, and the backend detail endpoint uses numeric `run_id`.
   - Alternative considered: coerce the route id to a number before calling the API. Rejected because the backend already provides stable validation/error behavior, and keeping the route id as a path segment preserves the current lightweight routing style.

2. Add a dedicated `getBacktestDetail(runId)` helper and response types in `apps/web/src/api/client.ts`.
   - Rationale: page code should keep using shared endpoint helpers, matching existing Dashboard and Signal Detail patterns.
   - Alternative considered: call `apiRequest` directly from the page. Rejected because existing specs require page code to use shared client helpers.

3. Render only a compact metadata and metrics view from the detail response.
   - Rationale: COP-110 asks for core detail display, metadata, date range, status, and parameter summary. The equity curve is part of the API response but chart/table presentation can be handled by later issues.
   - Alternative considered: show a raw equity curve preview. Rejected because it would add UI scope beyond COP-110.

4. Treat HTTP 404 as a stable missing-run state and other failures as API-unavailable states.
   - Rationale: COP-110 explicitly requires a stable error/empty state when a run does not exist.
   - Alternative considered: use one generic error message for all failures. Rejected because missing data and unavailable API need different user guidance.

## Risks / Trade-offs

- Route ids can be non-numeric → Mitigation: call the real API and render the normalized not-found/API error state rather than adding a second frontend validation contract.
- Parameter JSON may be malformed or long → Mitigation: render the raw value as a concise preformatted summary and use a stable empty value when it is absent.
- Metrics can be null for running or failed runs → Mitigation: format null values as `Not available` instead of hiding fields.

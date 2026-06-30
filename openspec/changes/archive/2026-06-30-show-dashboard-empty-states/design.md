## Context

The Dashboard already reads `GET /api/dashboard` through the shared frontend API client and renders panels for market data, latest signal, and recent backtest state. Existing empty states identify missing records but do not consistently explain both the missing local data and the next local operation.

## Goals / Non-Goals

**Goals:**
- Make the three Dashboard empty states explicit enough for local first-time use.
- Keep the copy tied to local CLI/API workflow actions.
- Validate the empty workflow response through the real dashboard API contract.

**Non-Goals:**
- Add interactive operation execution from the Dashboard.
- Change the dashboard API response shape.
- Add login, account, remote deployment, or multi-user assumptions.

## Decisions

- Keep empty-state behavior in `DashboardPage.tsx`.
  - Rationale: this is presentational behavior for the existing aggregate response, and no new backend state is required.
  - Alternative considered: add backend-provided empty-state messages. That would expand the API contract without a current need.

- Use disabled operation buttons as local next-step labels.
  - Rationale: the Dashboard already exposes disabled operation actions, so the empty states can reinforce the same local workflow without implementing command execution.
  - Alternative considered: render links or enabled actions. That would imply workflow execution that is outside this COP.

- Validate empty API data with an API integration test against `GET /api/dashboard`.
  - Rationale: the acceptance criteria requires real API empty data validation, and a FastAPI `TestClient` with a temporary empty SQLite database verifies the API contract without introducing a browser or dev-server dependency.

## Risks / Trade-offs

- Empty states remain instructional, not executable -> Mitigation: keep buttons disabled and copy clear that the user should run the local operation next.
- API integration validation does not prove visual rendering -> Mitigation: keep frontend tests responsible for rendering copy and disabled entry points, while API tests prove the real empty response shape.

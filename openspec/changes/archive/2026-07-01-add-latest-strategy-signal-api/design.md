## Context

The API service already exposes local FastAPI endpoints backed by request-scoped SQLite sessions. COP-98 added `POST /api/strategy-signals/generate`, which persists `StrategySignal` and `StrategySignalPosition` rows through existing core generation logic. The core package also has text report export logic that can locate and format the latest successful signal, but the frontend needs structured JSON rather than a text report.

## Goals / Non-Goals

**Goals:**

- Expose `GET /api/strategy-signals/latest` as a read-only query endpoint.
- Return structured latest successful signal metadata, fallback status, and positions.
- Return `200 OK` with a stable empty shape when no successful signal exists.
- Reuse or extract core latest signal query/serialization behavior so API routes stay thin.
- Validate with real persisted `StrategySignal` and `StrategySignalPosition` data in SQLite.

**Non-Goals:**

- Do not add a `signalDate` filter.
- Do not change signal generation behavior.
- Do not change Dashboard aggregate response shape in this COP.
- Do not add database tables, migrations, or dependencies.

## Decisions

1. Use `GET /api/strategy-signals/latest`.
   - Rationale: this is a read-only query and matches the `/api/strategy-signals` resource prefix selected for COP-98.
   - Alternative considered: `GET /api/signals/latest`, which is shorter but less aligned with the persisted `StrategySignal` model and COP-98 endpoint.
   - Alternative considered: adding positions to `GET /api/dashboard`, which would couple detail page data to the dashboard aggregate.

2. Return stable empty state with `200 OK`.
   - Rationale: first-run and empty local database states are normal frontend empty states, not exceptional failures.
   - Alternative considered: `404 Not Found`, which is semantically defensible but would force Dashboard and detail pages into error handling for an expected empty state.

3. Keep latest signal read behavior in `vela_core`.
   - Rationale: querying, ETF identity enrichment, position ordering, and fallback calculation are domain read-model behavior already present in the text report path.
   - Alternative considered: building the structure directly in the API route, which would duplicate core logic and weaken the API service boundary.

## Risks / Trade-offs

- Core report code currently returns text only -> Extract a structured read model that the text report and API can share.
- Position rows require ETF metadata lookup -> Preserve the existing ETF enrichment behavior and validate with real `ETFInfo` rows.
- Empty state shape becomes API contract -> Cover it in API integration tests and OpenSpec requirements.

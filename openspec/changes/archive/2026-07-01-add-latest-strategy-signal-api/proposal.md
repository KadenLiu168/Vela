## Why

The Phase 1 frontend needs a structured JSON endpoint for the latest successful strategy signal so Dashboard and detail views can render signal metadata, fallback status, and target holdings without parsing the existing text report.

## What Changes

- Add a read-only `GET /api/strategy-signals/latest` endpoint.
- Return the latest successful persisted `StrategySignal` across dates, including structured signal metadata, fallback status, and positions.
- Return a stable empty `200 OK` response when no successful signal exists: `has_signal: false`, `signal: null`, and `positions: []`.
- Reuse or extract existing core strategy signal persistence/query logic so the API does not duplicate report-only behavior.
- Validate the endpoint with local FastAPI + SQLite integration tests using real `StrategySignal` and `StrategySignalPosition` rows.
- Do not add a `signalDate` filter in this COP.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `http-api-service`: Add a structured latest successful strategy signal read endpoint backed by persisted signal data.

## Impact

- Affected API: new `GET /api/strategy-signals/latest`.
- Affected code: FastAPI route wiring in `apps/api`, with reusable structured latest signal query/serialization in `vela_core`.
- Affected tests: API integration tests with temporary SQLite databases and persisted ORM rows.
- No database migration or new dependency is expected.

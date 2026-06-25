## Why

COP-83 gives the frontend a read-only API for confirming service availability and inspecting the current strategy configuration. Health already exists, but the API cannot yet expose the checked-in `strategy_v1.yaml` and ETF pool summary through the local service.

## What Changes

- Keep the existing `GET /api/health` endpoint unchanged.
- Add `GET /api/config` as a read-only endpoint.
- Load real checked-in configuration via `vela_core.load_app_config("config/strategy_v1.yaml")`.
- Return a minimal strategy summary and ETF pool summary for frontend display.
- Add integration tests that use real configuration files and existing config loading behavior.
- Do not add config editing, strategy calculation, database access, or business trading endpoints.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `http-api-service`: Add a read-only config endpoint that returns current strategy and ETF pool summaries.

## Impact

- Updates API routes and response shaping under `apps/api/src/vela_api`.
- Adds API integration tests for `GET /api/config`.
- Updates API documentation and `http-api-service` OpenSpec requirements.

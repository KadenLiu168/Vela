## Why

COP-81 adds the local HTTP API entrypoint needed by the web frontend. The repository currently has an `apps/api` placeholder but no runnable service, health endpoint, or API package wiring.

## What Changes

- Add an `apps/api` FastAPI application skeleton.
- Add `fastapi` and `uvicorn` runtime dependencies.
- Add a root-level project command, `uv run vela-api`, for starting the API service.
- Add a minimal `GET /api/health` endpoint for frontend/local service checks.
- Add tests and documentation for the service skeleton.
- Keep API behavior limited to wrapping/exposing application entrypoints; do not implement strategy logic or business endpoints in this change.

## Capabilities

### New Capabilities

- `http-api-service`: Defines the local HTTP API service skeleton, startup command, and health endpoint.

### Modified Capabilities

- None.

## Impact

- Updates `pyproject.toml` and `uv.lock` for FastAPI, uvicorn, the TestClient dev dependency, API package discovery, and the `vela-api` console script.
- Adds API source under `apps/api/src/vela_api`.
- Adds API tests under `apps/api/tests`.
- Updates API and repository documentation for startup and health-check commands.

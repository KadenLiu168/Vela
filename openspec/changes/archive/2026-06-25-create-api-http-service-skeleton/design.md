## Context

`apps/api` currently contains only a placeholder README. COP-81 introduces a local HTTP service entrypoint so the web frontend has a stable API target while keeping strategy and data-processing logic inside `vela_core`.

## Goals / Non-Goals

**Goals:**

- Create a minimal FastAPI application under `apps/api`.
- Add a root-level startup command: `uv run vela-api`.
- Provide `GET /api/health` for local service checks.
- Add tests proving the health endpoint and app wiring work.
- Keep the API package discoverable through the existing Python packaging setup.

**Non-Goals:**

- Do not add strategy, market data, signal, backtest, authentication, or persistence endpoints.
- Do not duplicate or move `vela_core` business logic into `apps/api`.
- Do not introduce production deployment, process management, or reverse proxy configuration.

## Decisions

- Use FastAPI with uvicorn.
  - FastAPI fits the existing pydantic-oriented Python stack and gives a typed API foundation for later frontend work.
  - Flask was rejected because schema-oriented API evolution would require more manual conventions.
  - stdlib `http.server` was rejected because it is not a durable API service foundation.
- Add `uv run vela-api` as the project startup command.
  - This keeps the API app independent from the existing `vela` CLI while preserving the root-level `uv run ...` project convention.
  - The command will run uvicorn against the FastAPI app with local development defaults.
- Use `GET /api/health`.
  - This aligns the API service with the web frontend's default `/api` base URL.
  - `/health` will not be added as an alias in this change to keep the endpoint surface minimal.

## Risks / Trade-offs

- New runtime dependencies increase the backend dependency set -> Keep additions limited to FastAPI and uvicorn.
- `vela-api` exposes uvicorn behavior through a project command -> Keep the command thin and documented.
- Future endpoints may need shared response schemas -> Defer schema modules until an endpoint actually needs them.

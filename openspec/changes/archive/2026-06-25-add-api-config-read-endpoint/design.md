## Context

The API already exposes `GET /api/health`. The frontend also needs a read-only way to display the active local strategy configuration and ETF universe without reading files directly.

## Goals / Non-Goals

**Goals:**

- Keep `GET /api/health` unchanged.
- Add `GET /api/config`.
- Load real checked-in configuration from `config/strategy_v1.yaml` through `vela_core.load_app_config`.
- Return a compact strategy summary and ETF pool summary.
- Verify the endpoint with the real configuration files.

**Non-Goals:**

- Do not add config editing.
- Do not calculate strategy signals or backtests.
- Do not read from or write to the database.
- Do not add authentication or user-specific config.

## Decisions

- Use `GET /api/config` for the endpoint path.
  - It matches the existing `/api` prefix and clearly identifies a read-only config resource.
- Keep response shaping in the API layer.
  - `vela_core` already owns loading and validating configuration; the API should only serialize a frontend-friendly summary.
- Include ETF identity and metadata in the pool summary.
  - This gives the frontend enough information to display the current ETF pool and confirm that the defensive asset is included.

## Risks / Trade-offs

- Response shape may need expansion later -> Keep this response intentionally small and add fields only when a frontend issue needs them.
- Config path is currently fixed -> Use the checked-in `config/strategy_v1.yaml` for this first local-only API and defer runtime config selection.
- Chinese ETF names are returned as loaded from YAML -> Preserve source configuration values without translation.

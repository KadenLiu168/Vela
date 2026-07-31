## Why

The FastAPI service currently defines every route and manual response serializer in one module, and
most success responses are exposed to OpenAPI only as unconstrained objects. The service also
re-reads and validates the same checked-in strategy configuration on routine requests, making API
contracts harder to inspect, reuse, and evolve safely.

## What Changes

- Split HTTP routes into domain routers for configuration/dashboard, market data/setup, strategy
  signals, and backtests while retaining one application composition entry point.
- Define Pydantic success response models for every endpoint and register them as FastAPI response
  models so OpenAPI describes concrete fields and nesting.
- Preserve all current route paths, query parameters, status codes, JSON keys, list ordering,
  nullability, datetime representation, and Decimal-as-string payloads.
- Load and validate one immutable `AppConfig` during application lifespan for routine endpoint
  dependencies, with an explicit override seam for deterministic tests.
- Preserve the local bootstrap endpoint's existing request-scoped config reload so editing the ETF
  pool and invoking bootstrap does not require an API restart.
- Add route-inventory, OpenAPI-schema, response-validation, config-lifecycle, and API/Web contract
  regression coverage.
- Keep domain exception changes, request-id, and operational logging outside this Change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `http-api-service`: The existing HTTP surface gains domain-router composition, concrete typed
  success schemas, and application-scoped configuration injection without changing wire payloads.

## Impact

- Affected code: `apps/api/src/vela_api/` application composition, dependencies, routers, response
  schemas/serializers, and API tests; Web contract tests may be updated only where needed to prove
  compatibility.
- Affected runtime: routine API config reads move from per-request disk parsing to lifespan state;
  bootstrap retains its documented per-request reload.
- Unchanged: endpoint URLs and methods, request/query contracts, error envelope/mapping, core domain
  workflows, CLI config loading, database schema/data, and frontend-visible JSON values.
- Dependencies: uses existing FastAPI and Pydantic dependencies; no new package.

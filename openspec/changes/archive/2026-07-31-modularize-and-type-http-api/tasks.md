## 1. Lock the Existing HTTP Contract

- [x] 1.1 Add a complete application-owned method/path inventory regression, including static and
  parameterized signal/backtest routes and the `vela_api.main:app` import path.
- [x] 1.2 Add exact success-payload tests for system/config/dashboard, ETF/market-data/bootstrap,
  strategy-signal, and backtest endpoint families, covering Decimal strings, dates, datetimes,
  nullable fields, and empty arrays.
- [x] 1.3 Add failing OpenAPI tests requiring concrete success schemas and explicit nested/list
  field types instead of unconstrained object responses.
- [x] 1.4 Add failing config-lifecycle tests proving one startup load is reused by routine requests,
  invalid config prevents startup, dependency overrides are app-scoped, and bootstrap still reloads
  config once per request.

## 2. Introduce Application Composition and Config Dependency

- [x] 2.1 Add a `create_app()` application factory that initializes database state, registers the
  existing exception handlers, includes routers, and keeps `vela_api.main:app` compatible.
- [x] 2.2 Add a lifespan context that loads one immutable `AppConfig` and an overridable dependency
  that supplies it to routine endpoints without per-request YAML access.
- [x] 2.3 Update affected API test fixtures to use context-managed lifespan or explicit config
  dependency overrides and prove state/overrides do not leak between app instances.
- [x] 2.4 Keep `POST /api/setup/bootstrap` on its existing request-scoped `load_app_config` path and
  preserve current invalid-config behavior.

## 3. Define Typed Success Response Models

- [x] 3.1 Define system, configuration, and dashboard response models plus domain-local conversion
  helpers that preserve every existing key and serialized value.
- [x] 3.2 Define ETF price, market-data fetch, and bootstrap response models, including nested steps,
  nullability, counts, and current date/Decimal representations.
- [x] 3.3 Define strategy-signal list/latest/detail/generate response models, including provenance,
  positions, fallback fields, and empty states.
- [x] 3.4 Define backtest list/run/detail/metrics/equity/signal-page response models, preserving
  Decimal strings, signal counts/ids, ordering, and nullable metrics.
- [x] 3.5 Register every endpoint's success `response_model`, forbid unintended extra fields where
  API construction owns the payload, and make all OpenAPI contract tests pass.

## 4. Split Domain Routers Without Behavior Changes

- [x] 4.1 Move health/config/dashboard routes into the system router while preserving handler names,
  dependencies, paths, and payloads.
- [x] 4.2 Move ETF price, market-data fetch, and local setup routes into the market/setup router
  without changing provider injection, database transactions, or bootstrap orchestration.
- [x] 4.3 Move strategy-signal routes into the signal router, retaining static/detail registration
  order, query validation, core delegation, and current error mapping.
- [x] 4.4 Move backtest routes into the backtest router, retaining query aliases/bounds, SQL
  ordering/scoping, synchronous execution, and current error mapping.
- [x] 4.5 Reduce the main composition module to application construction/registration concerns and
  confirm no domain workflow or duplicate endpoint remains there.

## 5. Documentation and Verification

- [x] 5.1 Document that routine endpoint configuration is fixed for one API lifespan and requires a
  restart to refresh, while local bootstrap intentionally reloads configuration per request.
- [x] 5.2 Run focused API config, contract, error, dashboard, ETF, market-data, signal, backtest,
  bootstrap, database-session, and health tests.
- [x] 5.3 Run the complete Python CI-equivalent gate: `uv sync --group dev`,
  `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`,
  `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 5.4 Run target and global strict OpenSpec validation, `openspec doctor`, and `git diff --check`;
  inspect the final route inventory/OpenAPI document and confirm no Web payload, database schema, or
  persistent data changed.

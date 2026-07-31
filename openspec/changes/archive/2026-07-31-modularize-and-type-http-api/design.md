## Context

`apps/api/src/vela_api/main.py` currently owns application construction, exception handlers,
dependencies, 14 route functions, database queries for some endpoints, response serialization, and
formatting helpers. Most handlers declare `dict[str, object]`, so FastAPI emits generic
`additionalProperties` response schemas and does not validate successful payloads against an
explicit transport contract.

Routine endpoints also call `load_strategy_config` or `load_app_config` for every request even
though the checked-in application configuration is expected to be stable for one local API
process. The local bootstrap endpoint is intentionally different: its existing contract reloads
configuration for each invocation so a developer can edit the ETF pool and synchronize without
restarting.

The current HTTP paths, payloads, Decimal strings, date/datetime strings, error envelope, database
session ownership, and test dependency overrides are compatibility constraints.

## Goals / Non-Goals

**Goals:**

- Compose the existing API from small domain routers without changing its route inventory.
- Give every successful endpoint a concrete Pydantic response model and useful OpenAPI schema.
- Preserve exact frontend-visible JSON values and nesting.
- Load one validated immutable `AppConfig` for routine requests during application lifespan.
- Retain explicit dependency override seams for deterministic tests.
- Preserve bootstrap's request-scoped configuration reload.
- Leave a small composition module that remains import-compatible as `vela_api.main:app`.

**Non-Goals:**

- Adding, removing, versioning, or renaming endpoints.
- Changing domain workflows, SQL queries, pagination, status codes, or error mapping.
- Introducing typed domain exceptions, request-id, metrics, or new operational logs.
- Generating frontend TypeScript clients or replacing the existing Web API client.
- Hot-reloading routine API configuration through file watching or mtime caches.
- Changing CLI configuration loading.

## Decisions

### Use an application factory with a lifespan-owned config

`create_app()` will create the FastAPI instance, initialize its database state, register existing
exception handlers, include routers, and install a lifespan context that loads one `AppConfig`.
`vela_api.main` will continue exporting `app = create_app()` for uvicorn and tests.

A `get_app_config(Request)` dependency will return the lifespan-owned immutable config, and routine
endpoints will depend on it rather than reading YAML. Tests will override this dependency with a
validated test-owned `AppConfig`, and tests exercising lifespan will use `TestClient` as a context
manager.

A module-level `lru_cache` was rejected because it leaks state across app instances/tests and makes
startup failure less explicit. Mtime/watchdog reload was rejected because config hot reload is not
a routine API requirement.

### Preserve request-scoped reload for bootstrap

`POST /api/setup/bootstrap` will continue calling `load_app_config` once at request start and pass
that value to `run_local_setup_bootstrap`. It will not use the lifespan dependency. This preserves
the existing local workflow and avoids silently changing the `local-setup-bootstrap` capability.

### Organize routers by HTTP domain

The API package will contain routers for:

- system/config/dashboard;
- ETF and market-data/setup operations;
- strategy signals; and
- backtests.

Route functions will keep their existing names, methods, paths, query aliases, bounds, and
registration ordering where static and parameterized paths could overlap. Router modules may
perform the same HTTP-layer queries and orchestration they do today; this Change does not create a
new service/repository abstraction.

Splitting one file per endpoint was rejected as excessive fragmentation. Keeping all serializers in
one new giant `schemas.py` was also rejected; response models and domain conversion helpers will be
grouped by domain.

### Model the wire contract, not the ORM model

Pydantic response models will represent the existing JSON contract explicitly. ORM/domain objects
will be converted by small domain-local constructors or serializers rather than exposed directly.
Fields currently serialized as decimal strings will remain schema type `string` and JSON strings.
Dates/datetimes will retain their current textual values and receive appropriate OpenAPI formats
only where doing so does not alter serialization.

Success response validation is intentional: returning a missing or wrongly typed field becomes a
server-side contract failure instead of silently emitting an undocumented payload. Pydantic models
will forbid unexpected fields where construction is owned by the API so response drift is caught.

Using `Decimal` fields with default JSON serialization was rejected because it could alter the
frontend-visible representation or produce ambiguous generated client types.

### Preserve the current error system for the follow-up Change

The existing exception handlers and stable error envelope remain behaviorally unchanged. This
Change may relocate registration code only as needed by the application factory. Typed domain
exceptions, correlation ids, and logging belong to
`add-api-error-and-request-observability`, which will build on this structure.

### Verify route and payload compatibility explicitly

Tests will capture:

- the complete `(path, method)` route inventory;
- concrete OpenAPI response schemas for representative nested/list/nullable responses;
- exact existing success JSON for all endpoint families;
- Decimal, date, datetime, null, and empty-list serialization;
- one lifespan config load shared by routine requests;
- dependency override isolation across app instances; and
- bootstrap's separate per-request reload.

## Risks / Trade-offs

- [Router movement changes route precedence or operation ids] → Preserve handler names and router
  registration order; assert the complete method/path inventory and key OpenAPI operations.
- [Pydantic changes Decimal or datetime JSON] → Define transport field types/serializers explicitly
  and compare exact response bodies before and after.
- [Lifespan is skipped by existing tests] → Convert relevant tests to context-managed `TestClient`
  or override the config dependency explicitly.
- [Global app state leaks between tests] → Use an application factory and per-app overrides/state;
  clear overrides in fixture teardown.
- [Routine config edits are not visible until restart] → Document lifespan semantics; retain
  bootstrap's request-scoped reload for the intentional edit-and-sync workflow.
- [The structural change obscures business modifications] → Prohibit domain/SQL/error behavior
  changes and review the diff against the existing endpoint contract tests.

## Migration Plan

Implement response contract tests first, add the application factory/config dependency, introduce
domain response models, then move one endpoint family at a time into routers. Keep
`vela_api.main:app` throughout so uvicorn and scripts do not need migration. No database or
persisted-data migration is required. Rollback is a code-only revert.

## Open Questions

None. The follow-up error/observability Change is intentionally dependent on this Change's final
application and router structure.

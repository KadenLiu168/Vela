## Context

The API app already exposes the Phase 1 endpoint surface and has endpoint-specific tests under `apps/api/tests/`. COP-120 added shared SQLite integration data helpers under `tests/integration_data.py`, which gives this change a reusable way to exercise real FastAPI routes and persistence-backed workflows.

## Goals / Non-Goals

**Goals:**

- Add explicit API contract tests for health, config, dashboard, market data fetch, strategy signal, and backtest endpoints.
- Validate both response structure and key error envelopes through `TestClient`.
- Use temporary SQLite databases and shared integration data helpers for persistence-backed API paths.
- Keep provider substitution limited to controlled provider tests where the external market data source would otherwise make the test nondeterministic.

**Non-Goals:**

- Do not add or change production API routes.
- Do not change ORM models, migrations, or runtime dependencies.
- Do not mock out `vela_core` as the only validation path for workflow endpoints.
- Do not add frontend tests in this COP.

## Decisions

- Add a focused API contract test module in `apps/api/tests/`.
  - Rationale: the current files are endpoint-specific; a contract module makes COP-121's cross-endpoint coverage visible without refactoring existing tests.
  - Alternative considered: expanding only existing endpoint-specific files. That would work, but it makes it harder to see that the issue acceptance criteria are covered as a single interface-test surface.
- Reuse shared integration data helpers for SQLite setup.
  - Rationale: this follows COP-120 and avoids duplicated schema setup or endpoint-local fixture code.
  - Alternative considered: isolated ad hoc setup in each test. That would increase duplication and drift from the shared integration data capability.
- Keep production code changes out unless tests reveal an actual contract gap.
  - Rationale: COP-121 is about interface test coverage, and existing implementation already exposes the required API paths.

## Risks / Trade-offs

- Broader API tests can overlap existing endpoint tests -> keep assertions focused on contract shape and missing acceptance paths.
- Real workflow tests can be slower than pure unit tests -> use small deterministic SQLite datasets and controlled providers.
- Shared FastAPI app state can leak between tests -> reset `initialize_database(app, database_url=DEFAULT_DATABASE_URL)` and clear dependency overrides in `finally` blocks.

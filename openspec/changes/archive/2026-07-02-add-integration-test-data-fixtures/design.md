## Context

COP-120 targets integration test data preparation for the first-phase frontend work. Current API tests already use temporary SQLite databases, but setup helpers are duplicated across endpoint tests. The frontend API integration test can call a running local API, but it does not define how the API database is prepared before those calls.

The change should make real persistence validation easier without adding production behavior. API tests can reuse Python helpers directly. Frontend acceptance can prepare the same SQLite state before starting `uv run vela-api` or before running API client integration tests against an already configured local API.

## Goals / Non-Goals

**Goals:**
- Provide one shared Python test-support module that initializes SQLite schemas and seeds deterministic workflow data.
- Include minimal ETF metadata, market prices, latest signal rows, and backtest rows suitable for dashboard, signal, and backtest acceptance.
- Provide a controlled market data provider for fetch endpoint tests while keeping signal, dashboard, and backtest validation on persisted SQLite rows.
- Document the command sequence for frontend API integration validation against the prepared local database.

**Non-Goals:**
- Do not add a production seed command or production API endpoint.
- Do not change ORM models, migrations, or business workflow behavior.
- Do not require external market data providers for deterministic integration validation.
- Do not replace focused frontend unit tests that intentionally mock browser `fetch`.

## Decisions

- Put reusable setup in `tests/integration_data.py`.
  - Rationale: the helpers are test infrastructure shared by API tests and repository-level validation, not production `vela_core` behavior.
  - Alternative considered: putting helpers under `apps/api/tests`. That would keep API tests local but make reuse by frontend/API acceptance documentation awkward.

- Seed through SQLAlchemy ORM models and `Base.metadata.create_all`.
  - Rationale: COP-120 needs real SQLite persistence paths while staying lightweight for temporary test databases.
  - Alternative considered: invoking Alembic for every temporary test database. That is closer to production schema management but slower and unnecessary for current ORM-backed integration tests.

- Use controlled providers only for market data fetch tests.
  - Rationale: fetch tests need deterministic provider responses, while dashboard, signal, and backtest tests must prove persisted rows are read or written through SQLite.
  - Alternative considered: using the real AkShare provider. That would be non-deterministic and unsuitable for repeatable acceptance tests.

- Expose a small CLI entrypoint from the test-support module.
  - Rationale: frontend API integration validation can prepare a local SQLite database before starting the API without importing pytest fixtures.
  - Alternative considered: relying on manual SQL or copied setup snippets. That would recreate the inconsistency COP-120 is meant to remove.

## Risks / Trade-offs

- Test helpers could become too broad -> Keep only the minimal workflow dataset and endpoint-specific helpers needed by current integration validation.
- ORM `create_all` can diverge from migrations -> Keep this as test data preparation for temporary SQLite only; production/local development schema setup remains Alembic.
- Frontend integration still requires a separately running API process -> Document the exact database preparation and API startup sequence instead of hiding process orchestration in frontend tests.

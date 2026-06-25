## Context

The API service exists as a FastAPI skeleton with a health endpoint. COP-82 adds the database/session boundary needed by future business routes while keeping SQLAlchemy setup and lifecycle behavior in `vela_core.database`.

## Goals / Non-Goals

**Goals:**

- Share the default local SQLite URL from `vela_core.database`.
- Configure the API app with an engine and session factory built from that default URL.
- Provide a FastAPI request dependency that yields a SQLAlchemy `Session`.
- Reuse `managed_session` so successful requests commit, failed requests roll back, and all sessions close.
- Verify behavior with local SQLite integration tests, not mocks alone.

**Non-Goals:**

- Do not add business API routes.
- Do not introduce a full application settings layer.
- Do not change SQLAlchemy model definitions or Alembic migrations.

## Decisions

- Add `DEFAULT_DATABASE_URL = "sqlite+pysqlite:///vela.db"` to `vela_core.database`.
  - This removes the existing CLI-only ownership of the default URL and lets API and CLI reuse one source of truth.
- Store the API session factory on `app.state.session_factory`.
  - This keeps app-level wiring explicit and lets tests override the session factory without changing global state.
- Implement session handling as a FastAPI `yield` dependency.
  - It composes naturally with route handlers and avoids middleware-level assumptions before business routes exist.
  - The dependency delegates commit/rollback/close behavior to `managed_session`.

## Risks / Trade-offs

- App state is dynamically typed -> Keep the state key small and covered by integration tests.
- Tests need temporary SQLite databases -> Use file-backed SQLite URLs to exercise the same local database path style as production defaults.
- Future settings may supersede the default URL -> Keep this change minimal and defer environment configuration until required.

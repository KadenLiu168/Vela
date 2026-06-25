## Why

COP-82 makes the API service usable as a real local backend by connecting it to the same SQLite/session primitives used by the core backend. This is a prerequisite for later business API routes without duplicating database or strategy logic in `apps/api`.

## What Changes

- Add a shared default local SQLite database URL in `vela_core.database`.
- Update CLI code to use the shared default database URL instead of defining its own duplicate constant.
- Add API database wiring that creates a SQLAlchemy engine and session factory from the default database URL.
- Add a FastAPI request-scoped database session dependency that reuses `vela_core.database.managed_session`.
- Add integration tests using the API app, a temporary local SQLite database, and the real `vela_core.database` session utilities.
- Do not add business API endpoints or duplicate strategy logic.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `http-api-service`: Add API database wiring and request-scoped session lifecycle behavior.
- `database-session`: Add a shared default local SQLite database URL for applications to reuse.

## Impact

- Updates `packages/core/src/vela_core/database.py` and CLI usage of the default database URL.
- Adds API dependency/session wiring under `apps/api/src/vela_api`.
- Adds API integration tests under `apps/api/tests`.
- Updates OpenSpec specs for `http-api-service` and `database-session`.

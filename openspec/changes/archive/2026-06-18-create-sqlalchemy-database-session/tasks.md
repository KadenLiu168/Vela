## 1. Tests

- [x] 1.1 Add `packages/core/tests/test_database.py` coverage for creating a SQLAlchemy engine from a database URL.
- [x] 1.2 Add coverage for creating a session factory bound to an engine.
- [x] 1.3 Add coverage that managed sessions commit successful work and close the session.
- [x] 1.4 Add coverage that managed sessions roll back failed work, close the session, and re-raise the exception.
- [x] 1.5 Add coverage that managed sessions close after read-only work.

## 2. Core Implementation

- [x] 2.1 Add `packages/core/src/vela_core/database.py` with typed engine and session factory helpers.
- [x] 2.2 Add a typed managed session context manager that accepts a session factory.
- [x] 2.3 Keep the public API free of import-time database connections or global sessions.

## 3. Verification

- [x] 3.1 Run `uv run pytest packages/core/tests/test_database.py`.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run `uv run ruff check packages/core/src packages/core/tests`.
- [x] 3.4 Run `uv run mypy packages/core/src packages/core/tests`.

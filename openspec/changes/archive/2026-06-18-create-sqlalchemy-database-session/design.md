## Context

The repository currently has a small `vela_core` package with logging support and tests, while `pyproject.toml` already includes `sqlalchemy`. Upcoming ETF metadata and market data storage work needs a shared persistence foundation before individual repositories or services are added.

This change introduces the minimal database session layer in the core package: engine creation, session factory creation, and a context-managed session boundary.

## Goals / Non-Goals

**Goals:**

- Provide a reusable SQLAlchemy engine and `Session` factory setup for backend code.
- Provide a context manager that commits on success, rolls back on failure, and always closes the session.
- Keep the implementation testable with SQLite, including in-memory databases.
- Keep public APIs typed and small.

**Non-Goals:**

- Define ORM models or database tables.
- Add migrations or Alembic.
- Add repository classes for ETF metadata or market prices.
- Add production deployment configuration.

## Decisions

1. Put the session module under `packages/core/src/vela_core/database.py`.

   Rationale: database access is a core backend concern and should be reusable by CLI, API, and future packages. A single module is enough for this change; a package split would add structure before there is enough persistence code to justify it.

   Alternative considered: create `vela_core/db/session.py`. This is more extensible, but premature for a first session primitive.

2. Expose explicit factory functions instead of module-level global sessions.

   Rationale: tests and applications need to supply different database URLs. Factory functions also avoid hidden engine creation at import time.

   Alternative considered: a single global engine and `SessionLocal`. This is common in examples, but makes tests and multiple runtime configurations harder to isolate.

3. Use a context-managed session boundary for transaction handling.

   Rationale: callers should get one simple pattern for write operations. The context manager can commit successful work, roll back exceptions, and close sessions consistently.

   Alternative considered: require callers to manage commit, rollback, and close manually. That is flexible but duplicates boilerplate and makes transaction mistakes easier.

4. Use SQLAlchemy's synchronous engine and session APIs.

   Rationale: Phase 1 backend work does not require async database access, and synchronous SQLAlchemy is simpler to test and operate for CLI and batch workflows.

   Alternative considered: async SQLAlchemy. It adds event loop and driver constraints without a current requirement.

## Risks / Trade-offs

- Session context commits automatically on successful exit -> tests must cover rollback and commit behavior so callers understand the boundary.
- SQLite and production databases differ in connection behavior -> keep engine options injectable and avoid SQLite-specific behavior in the public API.
- No migration framework is included -> future model/table changes will need a separate migration capability before schema evolution becomes necessary.

## Why

Local development currently has SQLAlchemy models and Alembic migrations, but no single project command that prepares the SQLite database before running future ingestion, signal, or backtest workflows. A dedicated `init-db` CLI command gives contributors a clear first step for creating or updating the local development database.

## What Changes

- Add a CLI command named `init-db` for initializing the local SQLite database.
- Make the command idempotent: running it against an already-initialized database succeeds and leaves the database at the current Alembic head.
- Use the existing Alembic migration stack as the source of truth for schema creation.
- Print clear success and failure messages suitable for local development setup.

## Capabilities

### New Capabilities
- `cli-database-initialization`: CLI behavior for initializing the local development database.

### Modified Capabilities
- None.

## Impact

- Adds a CLI application entrypoint under `apps/cli` or an equivalent project script entrypoint.
- Adds CLI tests for successful initialization, idempotent reruns, and failure reporting.
- Reuses existing Alembic configuration and migrations.
- May add a small CLI dependency only if the implementation needs one; a standard-library CLI is acceptable if it remains simple.

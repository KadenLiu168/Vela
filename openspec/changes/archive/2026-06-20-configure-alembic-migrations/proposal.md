## Why

Vela already has SQLAlchemy models and Alembic revision files, but migration behavior is only covered indirectly by individual model specs and tests. A dedicated migration capability makes the database setup contract explicit before more persistence features depend on repeatable local schema setup.

## What Changes

- Define the project-level Alembic migration contract for ORM metadata discovery.
- Document and verify the SQLite local development migration flow from an empty database to the current head revision.
- Ensure migration checks cover both autogenerate metadata visibility and actual `upgrade head` execution.
- Bring developer-facing documentation in line with the existing database and ORM foundation.

## Capabilities

### New Capabilities
- `database-migrations`: Alembic configuration, ORM metadata discovery, migration generation, and SQLite local migration execution.

### Modified Capabilities
- None.

## Impact

- Affected code: `alembic.ini`, `alembic/env.py`, `alembic/versions/`, and migration-related tests.
- Affected documentation: README or developer docs that describe local SQLite migration commands.
- Dependencies: no new runtime dependency is expected; Alembic already exists in the dev dependency group.
- Systems: local development database setup for ETF metadata, market data, strategy signals, and backtesting persistence.

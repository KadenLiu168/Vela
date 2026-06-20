## Context

Vela already has SQLAlchemy ORM models, Alembic migration files, and a default SQLite URL in `alembic.ini`. The missing piece is an application-level command that a developer can run before using future local workflows. The command should prepare the database through the same migration path the project will use as schema changes accumulate.

The CLI application surface is still minimal: `apps/cli` currently has no implementation and `pyproject.toml` has no project script. This change should introduce only the smallest CLI structure needed for `init-db`.

## Goals / Non-Goals

**Goals:**
- Provide an `init-db` CLI command that initializes the local SQLite database for development.
- Keep the command idempotent by running Alembic to the current head.
- Print clear success and failure messages.
- Add focused tests for success, idempotency, and failure behavior.

**Non-Goals:**
- Add a full CLI command suite beyond `init-db`.
- Replace Alembic with direct `Base.metadata.create_all()` table creation.
- Add production database provisioning or deployment behavior.
- Add seed data or data ingestion.

## Decisions

1. Use Alembic `upgrade head` as the initialization mechanism.

   Rationale: Alembic migrations are already the project's schema source of truth. Running migrations creates new databases and updates existing databases through the same path.

   Alternative considered: call `Base.metadata.create_all()`. This is simpler for a brand-new SQLite file, but it bypasses migration history and can drift from real schema evolution.

2. Register a project script for the CLI entrypoint.

   Rationale: `uv run <script> init-db` or an equivalent project command is easier for local setup than invoking a Python module path. The implementation can still live under `apps/cli` to match the repository structure.

   Alternative considered: keep a script under `scripts/`. That would work for development, but it would not establish the CLI app entrypoint requested by the change.

3. Keep argument handling minimal.

   Rationale: The requested command only needs to initialize the local database. If a database URL override is added, it should exist to support tests and local setup without turning this into a general migration tool.

   Alternative considered: adopt a larger CLI framework immediately. That can be useful later, but it is unnecessary unless the implementation would otherwise become unclear or hard to test.

4. Treat repeated runs as success.

   Rationale: A local setup command should be safe to run multiple times. Alembic already makes `upgrade head` idempotent when the database is at head.

## Risks / Trade-offs

- Alembic output can be noisy or inconsistent across versions -> Wrap command-level output with a stable success/failure message and test that behavior.
- CLI tests could accidentally write `vela.db` in the repository root -> Use temporary database URLs/configuration in tests.
- Adding a CLI dependency too early could increase maintenance surface -> Prefer standard-library parsing unless a local pattern or clear testing benefit justifies a dependency.
- Directly mutating global Alembic configuration in tests can leak state -> Build configuration objects per invocation and keep tests isolated.

## Migration Plan

1. Add the CLI entrypoint and `init-db` implementation.
2. Add tests using a temporary SQLite database path.
3. Document the local development command in the CLI or project README.
4. No data migration is required because this change only adds a command that runs existing migrations.

Rollback is removing the CLI entrypoint and implementation; existing databases and Alembic migrations are unaffected.

## Open Questions

- None.

## Context

Vela currently uses SQLAlchemy ORM models under `packages/core/src/vela_core/models` and has Alembic configuration at the repository root. Existing model specs verify that Alembic can load individual tables through `target_metadata`, and existing revision files can migrate an empty SQLite database to the current schema.

The missing contract is project-level: developers need one documented migration entrypoint that proves Alembic sees all ORM metadata, can compare metadata for future revision generation, and can initialize a local SQLite database.

## Goals / Non-Goals

**Goals:**
- Keep Alembic as the single database migration entrypoint.
- Ensure Alembic imports the complete ORM model registry before exposing `Base.metadata`.
- Verify `upgrade head` works against an empty SQLite database.
- Document the local SQLite migration workflow for developers.

**Non-Goals:**
- Replace the existing revision history with one squashed baseline migration.
- Add production database configuration or deployment automation.
- Add async SQLAlchemy support.
- Change existing ORM schemas unless verification reveals a migration mismatch.

## Decisions

1. Keep the existing revision chain as the initial executable history.

   Rationale: The current chain records incremental model evolution and already upgrades an empty SQLite database to the current head. Squashing into a single baseline would create churn without improving the local developer workflow.

   Alternative considered: create one new full-schema baseline revision. That would be simpler to read but risks disconnecting existing revision IDs from archived model changes.

2. Use explicit model imports in Alembic `env.py`.

   Rationale: Alembic autogenerate only sees tables registered in `Base.metadata`. Explicit imports make discovery predictable and easy to test.

   Alternative considered: dynamically import every module under `vela_core.models`. That reduces manual maintenance but adds import-time complexity that is unnecessary for the current number of models.

3. Use SQLite as the documented local migration target.

   Rationale: The project is in Phase 1 and already uses SQLite-compatible models and tests. A file-backed SQLite database is enough for local development and command verification.

   Alternative considered: introduce environment-specific database URLs now. That is useful later, but Phase 1 does not require production deployment or multiple database backends.

4. Verify migrations with command-level tests or documented manual checks.

   Rationale: Metadata-only tests prove discovery, while `alembic upgrade head` proves the revision chain actually executes. Both are needed to satisfy the migration workflow contract.

   Alternative considered: rely only on `Base.metadata.create_all()`. That bypasses Alembic and would not catch broken revision ordering or downgrade/upgrade operations.

## Risks / Trade-offs

- Existing revisions may diverge from ORM metadata as models evolve -> add or keep a migration drift/autogenerate check for future changes.
- SQLite has weaker type and constraint behavior than production databases -> treat SQLite verification as local development coverage only, not proof of future production database compatibility.
- Explicit model imports can be missed when adding a model -> require tests that assert Alembic `target_metadata` includes every persisted model table.

## Migration Plan

1. Confirm Alembic has a single head revision.
2. Confirm Alembic target metadata includes all ORM tables.
3. Run `alembic upgrade head` against an empty SQLite database.
4. Document the local commands for creating or resetting the development SQLite database.
5. Rollback is limited to removing any documentation or test additions from this change; existing schema revisions should not be deleted unless a specific migration defect is found.

## Open Questions

- Should local development keep using the default `vela.db` path from `alembic.ini`, or should docs recommend overriding `sqlalchemy.url` for temporary test databases?

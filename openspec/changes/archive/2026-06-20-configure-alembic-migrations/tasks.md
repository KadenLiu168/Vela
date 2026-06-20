## 1. Alembic Metadata Discovery

- [x] 1.1 Audit `alembic/env.py` and `vela_core.models` exports to confirm every persisted ORM model is imported before `target_metadata` is assigned.
- [x] 1.2 Add or consolidate tests that assert Alembic target metadata includes all current persisted ORM tables.
- [x] 1.3 Verify the metadata test fails if a persisted model is omitted from Alembic discovery.

## 2. SQLite Migration Execution

- [x] 2.1 Add a test or script-level check that runs `alembic upgrade head` against an empty temporary SQLite database.
- [x] 2.2 Assert the migrated SQLite database records the current Alembic head revision.
- [x] 2.3 Assert the migrated SQLite database contains current persistence tables and excludes obsolete intermediate tables.

## 3. Revision Generation Readiness

- [x] 3.1 Run an Alembic autogenerate or drift check against the migrated SQLite schema.
- [x] 3.2 Confirm the current ORM metadata and current migration head do not produce unexpected schema changes.
- [x] 3.3 Document any intentional SQLite-specific limitations found during the check.

## 4. Developer Documentation

- [x] 4.1 Update developer-facing documentation with local SQLite migration commands.
- [x] 4.2 Clarify how to create, upgrade, and reset the local SQLite development database.
- [x] 4.3 Update stale project status text that still describes the database and ORM foundation as future work.

## 5. Verification

- [x] 5.1 Run the migration-focused tests.
- [x] 5.2 Run the full core test suite.
- [x] 5.3 Run `openspec status --change "configure-alembic-migrations"` and confirm the change remains valid for apply.

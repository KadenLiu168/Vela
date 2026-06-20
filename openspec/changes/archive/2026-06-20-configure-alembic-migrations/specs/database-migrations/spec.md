## ADDED Requirements

### Requirement: Alembic ORM metadata discovery
The system SHALL configure Alembic to expose SQLAlchemy ORM metadata containing every persisted Vela model table.

#### Scenario: Alembic loads project metadata
- **WHEN** Alembic imports the migration environment
- **THEN** the target metadata includes all persisted ORM model tables

#### Scenario: New persisted models are discoverable
- **WHEN** a persisted ORM model is added to the project
- **THEN** Alembic target metadata includes that model table before migration autogeneration is used

### Requirement: SQLite migration execution
The system SHALL support applying Alembic migrations from an empty local SQLite database to the current head revision.

#### Scenario: Upgrade empty SQLite database
- **WHEN** a developer runs Alembic upgrade against an empty SQLite database
- **THEN** Alembic applies the full revision chain successfully
- **AND** the database records the current head revision in `alembic_version`

#### Scenario: Migrated SQLite database has current tables
- **WHEN** Alembic upgrade completes against a local SQLite database
- **THEN** the database contains the current Vela persistence tables
- **AND** obsolete intermediate tables are not present at head

### Requirement: Migration generation readiness
The system SHALL support generating future Alembic revisions by comparing ORM metadata against the configured database schema.

#### Scenario: Autogenerate can inspect metadata
- **WHEN** Alembic autogenerate is invoked for a future schema change
- **THEN** Alembic can compare the configured database schema with `Base.metadata`

### Requirement: Local migration workflow documentation
The system SHALL document the local SQLite migration commands needed by developers.

#### Scenario: Developer initializes local database
- **WHEN** a developer follows the documented migration workflow
- **THEN** they can create or update a local SQLite development database to the current Alembic head

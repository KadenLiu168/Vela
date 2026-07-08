# database-migrations Specification

## Purpose
Define Vela's Alembic migration contract for SQLAlchemy ORM metadata discovery, local SQLite schema upgrades, and migration drift checks.
## Requirements
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

### Requirement: Strategy signal strategy_id column and backtest rename migration
The system SHALL provide a single Alembic revision that adds a non-null `strategy_id` column to `strategy_signal` (backfilling every existing row with the current strategy config's `strategy_id`), renames `backtest_run.strategy_name` to `strategy_id`, and normalizes the renamed column's values to the current strategy config's `strategy_id`.

#### Scenario: Fresh database upgrades to head
- **WHEN** a developer runs `alembic upgrade head` against an empty SQLite database
- **THEN** the `strategy_signal` table includes a non-null `strategy_id` column
- **AND** the `backtest_run` table has a `strategy_id` column and no `strategy_name` column

#### Scenario: Existing signal rows are backfilled
- **WHEN** the revision is applied to a database with existing `strategy_signal` rows
- **THEN** every pre-existing row's `strategy_id` equals the current strategy config's `strategy_id`

#### Scenario: Backtest column is renamed and values normalized
- **WHEN** the revision is applied to a database whose `backtest_run.strategy_name` contains lowercase, mixed-case, or canonical values
- **THEN** the column is renamed to `strategy_id`
- **AND** every row's `strategy_id` equals the current strategy config's `strategy_id`

#### Scenario: Backtest strategy index remains usable
- **WHEN** the revision completes
- **THEN** an index on `backtest_run(strategy_id, config_version)` exists for strategy-scoped queries


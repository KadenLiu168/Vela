# alembic-migration-runner Specification

## Purpose
TBD - created by archiving change decouple-core-from-alembic. Update Purpose after archive.
## Requirements
### Requirement: Reusable Alembic config builder
The system SHALL provide a `build_alembic_config(database_url, script_location)` function in `vela_core.migration` that constructs an `alembic.config.Config` with the given script location and database URL, as the single source of truth for Alembic configuration construction across the project.

#### Scenario: Build config with explicit script location and database URL
- **WHEN** a caller invokes `build_alembic_config(database_url="sqlite:///test.db", script_location=Path("/repo/alembic"))`
- **THEN** the returned `Config` has `script_location` set to `"/repo/alembic"`
- **AND** the returned `Config` has `sqlalchemy.url` set to `"sqlite:///test.db"`

### Requirement: Reusable Alembic upgrade runner
The system SHALL provide a `run_alembic_upgrade(database_url, script_location)` function in `vela_core.migration` that applies Alembic migrations to the current head revision, as the single reusable entry point for migration execution across bootstrap, CLI, and tests.

#### Scenario: Upgrade empty database to head
- **WHEN** a caller invokes `run_alembic_upgrade` against an empty SQLite database with a valid `script_location`
- **THEN** Alembic applies the full revision chain to the current head
- **AND** the database records the current head revision in `alembic_version`

#### Scenario: Upgrade already-current database is a no-op
- **WHEN** a caller invokes `run_alembic_upgrade` against a database already at the current Alembic head
- **THEN** the command succeeds without altering the schema
- **AND** no error is raised

### Requirement: Alembic import isolation
The system SHALL confine all `alembic` imports to the `vela_core.migration` module. No other module in `vela_core` SHALL import `alembic` directly.

#### Scenario: Bootstrap module does not import alembic
- **WHEN** a developer inspects the import statements of `packages/core/src/vela_core/bootstrap.py`
- **THEN** the module does not contain `from alembic import` or `import alembic`
- **AND** the module does not compute a project root path via `parents[N]`


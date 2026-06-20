# cli-database-initialization Specification

## Purpose
Define the CLI behavior for initializing Vela's local development database.

## Requirements
### Requirement: Initialize local database from CLI
The system SHALL provide an `init-db` CLI command that initializes the local SQLite database by applying the project's Alembic migrations to the current head revision.

#### Scenario: Initialize empty SQLite database
- **WHEN** a developer runs the `init-db` command against a missing local SQLite database file
- **THEN** the system creates the database and applies all Alembic migrations through the current head revision

#### Scenario: Re-run database initialization
- **WHEN** a developer runs the `init-db` command against a local SQLite database that is already at the current Alembic head revision
- **THEN** the command succeeds without changing the schema or reporting the run as a failure

### Requirement: Report initialization result
The system SHALL print clear command-line output for both successful and failed database initialization attempts.

#### Scenario: Successful initialization message
- **WHEN** the `init-db` command completes successfully
- **THEN** the system prints a success message that identifies the initialized database target

#### Scenario: Failed initialization message
- **WHEN** the `init-db` command cannot initialize the database
- **THEN** the system prints a failure message with the underlying error context and exits with a non-zero status

### Requirement: Support local development setup
The system SHALL expose `init-db` through the project CLI so it can be used as a local development setup command.

#### Scenario: Run setup command through project tooling
- **WHEN** a developer invokes the project CLI with the `init-db` command
- **THEN** the system runs database initialization without requiring direct Alembic command knowledge

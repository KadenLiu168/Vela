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

### Requirement: Fetch full market data from CLI
The system SHALL expose a CLI command that runs a full daily market data fetch for the active ETF universe.

#### Scenario: Run full market data fetch command
- **WHEN** a user invokes the project CLI full market data fetch command with a database URL
- **THEN** the system connects to that database and runs the full active ETF market price fetch workflow

#### Scenario: Use default local database target
- **WHEN** a user invokes the project CLI full market data fetch command without a database URL
- **THEN** the system uses the same default local SQLite database target as other local CLI database commands

### Requirement: Report full market data fetch result
The system SHALL print a clear command-line summary after a full market data fetch command finishes.

#### Scenario: Successful fetch summary
- **WHEN** the full market data fetch command completes with `success` status
- **THEN** the system prints the status, requested symbol count, fetched row count, inserted row count, and updated row count

#### Scenario: Partial fetch summary
- **WHEN** the full market data fetch command completes with `partial` status
- **THEN** the system prints the status, successful row counts, and failed symbols or error context

#### Scenario: Failed fetch summary
- **WHEN** the full market data fetch command completes with `failed` status
- **THEN** the system prints the failure status and error context and exits with a non-zero status


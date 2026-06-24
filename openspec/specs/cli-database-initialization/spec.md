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

### Requirement: Fetch incremental market data from CLI
The system SHALL expose an incremental mode on the market data fetch CLI command.

#### Scenario: Run incremental market data fetch command
- **WHEN** a user invokes the project CLI market data fetch command with incremental mode and a database URL
- **THEN** the system connects to that database and runs the incremental active ETF market price fetch workflow

#### Scenario: Keep full fetch as default mode
- **WHEN** a user invokes the project CLI market data fetch command without incremental mode
- **THEN** the system runs the existing full active ETF market price fetch workflow

#### Scenario: Use default local database target for incremental mode
- **WHEN** a user invokes the project CLI market data fetch command with incremental mode and without a database URL
- **THEN** the system uses the same default local SQLite database target as other local CLI database commands

### Requirement: Report incremental market data fetch result
The system SHALL print a clear command-line summary after an incremental market data fetch command finishes.

#### Scenario: Successful incremental fetch summary
- **WHEN** the incremental market data fetch command completes with `success` status
- **THEN** the system prints the status, requested symbol count, fetched row count, inserted row count, and updated row count

#### Scenario: Partial incremental fetch summary
- **WHEN** the incremental market data fetch command completes with `partial` status
- **THEN** the system prints the status, successful row counts, and failed symbols or error context

#### Scenario: Failed incremental fetch summary
- **WHEN** the incremental market data fetch command completes with `failed` status
- **THEN** the system prints the failure status and error context and exits with a non-zero status

### Requirement: Generate strategy signal from CLI
The system SHALL expose a `generate-signal` CLI command that generates and stores the latest local strategy signal.

#### Scenario: Run signal generation command
- **WHEN** a user invokes `generate-signal` with a database URL and strategy config path
- **THEN** the system connects to that database
- **AND** the system loads the strategy configuration
- **AND** the system generates and persists a strategy signal using local market prices

#### Scenario: Use default signal generation inputs
- **WHEN** a user invokes `generate-signal` without optional arguments
- **THEN** the system uses the same default local SQLite database target as other local CLI database commands
- **AND** the system uses the checked-in strategy v1 config file
- **AND** the system uses the latest local market price date as the signal date

### Requirement: Report generated strategy signal result
The system SHALL print a clear command-line summary after signal generation finishes.

#### Scenario: Successful signal summary
- **WHEN** the `generate-signal` command persists a successful strategy signal
- **THEN** the system prints the signal status, result, signal date, config version, signal id, and target positions

#### Scenario: Failed signal summary
- **WHEN** the `generate-signal` command cannot generate a successful strategy signal
- **THEN** the system prints the failure status and error context
- **AND** the command exits with a non-zero status

### Requirement: Export latest signal report from CLI
The system SHALL expose an `export-signal-report` CLI command that exports the latest successful persisted strategy signal report.

#### Scenario: Print latest signal report
- **WHEN** a user invokes `export-signal-report` with a database URL and strategy config path
- **THEN** the system connects to that database
- **AND** the system loads the strategy configuration
- **AND** the system prints a human-readable report for the latest successful signal for that config version

#### Scenario: Use default report inputs
- **WHEN** a user invokes `export-signal-report` without optional arguments
- **THEN** the system uses the same default local SQLite database target as other local CLI database commands
- **AND** the system uses the checked-in strategy v1 config file

#### Scenario: Export report to file
- **WHEN** a user invokes `export-signal-report` with an output file path
- **THEN** the system writes the human-readable report to that path
- **AND** the command prints a confirmation identifying the output path

#### Scenario: Report missing latest signal
- **WHEN** a user invokes `export-signal-report` and no matching successful strategy signal exists
- **THEN** the command prints a clear failure message
- **AND** the command exits with a non-zero status

### Requirement: Run backtest CLI command
The system SHALL expose a `run-backtest` CLI command that runs and persists a backtest for a strategy configuration and date range.

#### Scenario: Run backtest with explicit inputs
- **WHEN** a user invokes `run-backtest` with a database URL, strategy config path, start date, and end date
- **THEN** the command runs the backtest using those inputs
- **AND** persists the backtest result
- **AND** prints the persisted backtest run id and core metric summary

#### Scenario: Run backtest default inputs
- **WHEN** a user invokes `run-backtest` with start date and end date but without optional database URL or strategy config path
- **THEN** the command uses the default local database URL and checked-in strategy configuration path

#### Scenario: Run backtest failure
- **WHEN** the `run-backtest` command cannot complete the backtest
- **THEN** the command prints an error message to stderr
- **AND** exits with a non-zero status

### Requirement: Export backtest report from CLI
The system SHALL expose an `export-backtest-report` CLI command that exports a persisted backtest report by run id.

#### Scenario: Print backtest report
- **WHEN** a user invokes `export-backtest-report` with a database URL and run id
- **THEN** the system connects to that database
- **AND** prints a human-readable report for that backtest run

#### Scenario: Use default database
- **WHEN** a user invokes `export-backtest-report` with a run id but without a database URL
- **THEN** the system uses the same default local SQLite database target as other local CLI database commands

#### Scenario: Export backtest report to file
- **WHEN** a user invokes `export-backtest-report` with an output file path
- **THEN** the system writes the human-readable report to that path
- **AND** the command prints a confirmation identifying the output path

#### Scenario: Missing backtest run report
- **WHEN** a user invokes `export-backtest-report` for a run id that does not exist
- **THEN** the command prints a clear failure message
- **AND** the command exits with a non-zero status


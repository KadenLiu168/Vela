## ADDED Requirements

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

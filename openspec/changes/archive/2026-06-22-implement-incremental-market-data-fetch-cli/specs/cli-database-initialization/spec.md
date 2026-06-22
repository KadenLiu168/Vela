## ADDED Requirements

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

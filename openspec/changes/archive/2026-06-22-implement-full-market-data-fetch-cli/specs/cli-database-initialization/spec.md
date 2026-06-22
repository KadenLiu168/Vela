## ADDED Requirements

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

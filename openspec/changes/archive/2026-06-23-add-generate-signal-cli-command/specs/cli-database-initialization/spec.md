## ADDED Requirements

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

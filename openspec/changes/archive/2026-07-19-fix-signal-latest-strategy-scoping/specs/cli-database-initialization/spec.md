## MODIFIED Requirements

### Requirement: Export latest signal report from CLI
The system SHALL expose an `export-signal-report` CLI command that exports the latest successful
persisted strategy signal report for the `strategy_id` and `config_version` loaded from the
selected strategy configuration.

#### Scenario: Print latest signal report
- **WHEN** a user invokes `export-signal-report` with a database URL and strategy config path
- **THEN** the system connects to that database
- **AND** the system loads the strategy configuration
- **AND** the system prints a human-readable report for the latest successful signal whose
  `strategy_id` and `config_version` match that configuration
- **AND** it ignores signals belonging to other strategies or config versions

#### Scenario: Use default report inputs
- **WHEN** a user invokes `export-signal-report` without optional arguments
- **THEN** the system uses the same default local SQLite database target as other local CLI
  database commands
- **AND** the system uses the checked-in strategy v1 config file

#### Scenario: Export report to file
- **WHEN** a user invokes `export-signal-report` with an output file path
- **THEN** the system writes the human-readable report to that path
- **AND** the command prints a confirmation identifying the output path

#### Scenario: Report missing latest signal
- **WHEN** a user invokes `export-signal-report` and no successful signal matches the configured
  strategy id and config version
- **THEN** the command prints a clear failure message
- **AND** the command exits with a non-zero status

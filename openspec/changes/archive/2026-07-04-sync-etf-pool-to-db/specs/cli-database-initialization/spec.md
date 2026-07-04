## ADDED Requirements

### Requirement: Sync ETF pool from CLI
The system SHALL expose a `sync-etf-pool` CLI command that synchronizes the configured ETF pool into the local ETF metadata table.

#### Scenario: Run ETF pool sync command
- **WHEN** a user invokes `sync-etf-pool` with a database URL and strategy config path
- **THEN** the system connects to that database
- **AND** the system loads the strategy configuration and its referenced ETF pool
- **AND** the system synchronizes the ETF pool entries into `etf_info`

#### Scenario: Use default ETF pool sync inputs
- **WHEN** a user invokes `sync-etf-pool` without optional arguments
- **THEN** the system uses the same default local SQLite database target as other local CLI database commands
- **AND** the system uses the checked-in strategy v1 config file

### Requirement: Report ETF pool sync result
The system SHALL print a clear command-line summary after ETF pool synchronization finishes.

#### Scenario: Successful ETF pool sync summary
- **WHEN** the `sync-etf-pool` command completes successfully
- **THEN** the system prints the sync status, pool id, total ETF count, inserted row count, updated row count, and unchanged row count

#### Scenario: Failed ETF pool sync summary
- **WHEN** the `sync-etf-pool` command cannot load configuration or synchronize ETF metadata
- **THEN** the command prints a failure message with the underlying error context
- **AND** the command exits with a non-zero status

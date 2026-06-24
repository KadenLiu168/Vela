## ADDED Requirements

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

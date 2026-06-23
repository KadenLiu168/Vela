## ADDED Requirements

### Requirement: Generate historical strategy signals
The system SHALL generate strategy signals for historical rebalance dates by reusing the existing single-date strategy signal generation logic.

#### Scenario: Generate signals for historical rebalance dates
- **WHEN** backend code generates historical strategy signals from a sequence of historical trading dates
- **THEN** the system derives weekly rebalance dates from those trading dates
- **AND** the system generates one strategy signal for each derived rebalance date
- **AND** the generated results are returned in ascending signal date order

#### Scenario: Historical generation does not use future data
- **WHEN** backend code generates a historical strategy signal for a rebalance date that has later market prices available in storage
- **THEN** strategy calculations for that signal use only market data on or before that rebalance date

#### Scenario: Historical signal positions are persisted
- **WHEN** historical strategy signal generation produces target positions for a rebalance date
- **THEN** the database contains persisted strategy signal positions for that generated signal
- **AND** each persisted position includes the target weight needed by portfolio holding calculation

#### Scenario: Empty historical trading dates
- **WHEN** backend code generates historical strategy signals from an empty trading-date sequence
- **THEN** the system returns an empty result list
- **AND** no strategy signal rows are persisted

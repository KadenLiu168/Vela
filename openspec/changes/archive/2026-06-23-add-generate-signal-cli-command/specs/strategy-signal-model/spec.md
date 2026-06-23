## ADDED Requirements

### Requirement: Generated signal persistence
The system SHALL persist strategy signal generation results through the existing strategy signal persistence contract.

#### Scenario: Persist successful generated signal
- **WHEN** signal generation produces target positions
- **THEN** the database contains one successful `StrategySignal` row for that run
- **AND** the database contains one `StrategySignalPosition` row for each target position

#### Scenario: Persist failed generated signal
- **WHEN** signal generation cannot produce a valid signal
- **THEN** the database contains one failed `StrategySignal` row for that run
- **AND** the row includes the generation error message

## ADDED Requirements

### Requirement: Strategy signal persistence helper
The system SHALL provide a core helper that persists one `StrategySignal` row and its associated `StrategySignalPosition` rows in the same SQLAlchemy session.

#### Scenario: Persist signal with positions
- **WHEN** backend code persists a successful signal for a signal date, config version, generated timestamp, result, and target positions
- **THEN** the database contains one `StrategySignal` row with those signal fields and one `StrategySignalPosition` row for each target position

#### Scenario: Persist signal without positions
- **WHEN** backend code persists a signal result that has no target positions
- **THEN** the database contains the `StrategySignal` row and no child position rows for that signal

### Requirement: Strategy signal rerun persistence
The system SHALL preserve repeated generation for the same `signal_date` and `config_version` by creating a new strategy signal run instead of replacing prior runs.

#### Scenario: Same date and config version persisted twice
- **WHEN** backend code persists two signals with the same `signal_date` and `config_version`
- **THEN** the database contains two distinct `StrategySignal` rows

### Requirement: Latest successful strategy signal query
The system SHALL provide a core query helper that returns the latest successful strategy signal for a `signal_date` and `config_version` with its positions available.

#### Scenario: Latest successful signal exists
- **WHEN** backend code queries for a date and config version that have multiple successful strategy signal runs
- **THEN** the helper returns the successful run with the newest `generated_at` timestamp

#### Scenario: Latest successful signal ignores non-success rows
- **WHEN** backend code queries for a date and config version where a newer non-success run exists after an older successful run
- **THEN** the helper returns the older successful run

#### Scenario: Latest successful signal does not exist
- **WHEN** backend code queries for a date and config version that have no successful strategy signal run
- **THEN** the helper returns no signal

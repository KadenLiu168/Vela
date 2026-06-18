## ADDED Requirements

### Requirement: Strategy signal position ORM relationship
The system SHALL expose an explicit SQLAlchemy ORM relationship between `StrategySignal` and `StrategySignalPosition`.

#### Scenario: Signal exposes related positions
- **WHEN** backend code loads a `StrategySignal` with related position rows
- **THEN** `StrategySignal.positions` provides the `StrategySignalPosition` rows for that signal

#### Scenario: Position exposes parent signal
- **WHEN** backend code loads a `StrategySignalPosition`
- **THEN** `StrategySignalPosition.strategy_signal` provides the parent `StrategySignal`

#### Scenario: Relationship preserves existing table schema
- **WHEN** Alembic compares ORM metadata for this change
- **THEN** no new table or column is required for the relationship

# strategy-signal-model Specification

## Purpose

Define the strategy signal persistence contract used by strategy generation and historical backtesting.
## Requirements
### Requirement: Strategy signal ORM model
The system SHALL define a `StrategySignal` SQLAlchemy ORM model for one strategy signal generation run.

#### Scenario: Model exposes signal run fields
- **WHEN** backend code inspects the `StrategySignal` model table
- **THEN** the table includes columns for `id`, `signal_date`, `config_version`, `generated_at`, `status`, `result`, `error_message`, `created_at`, and `updated_at`

#### Scenario: Signal run status values
- **WHEN** backend code creates strategy signal rows for generation lifecycle states
- **THEN** the model supports `running`, `success`, `failed`, and `partial` status values

#### Scenario: Signal run result values
- **WHEN** backend code creates strategy signal rows for strategy judgements
- **THEN** the model supports `buy`, `hold`, `rebalance`, and `empty` result values

### Requirement: Strategy signal run history
The system SHALL preserve multiple strategy signal generation runs for the same signal date and configuration version.

#### Scenario: Same date and config version rerun
- **WHEN** two strategy signal rows use the same `signal_date` and `config_version` values
- **THEN** the database allows both rows

#### Scenario: Inspect strategy signal run indexes
- **WHEN** backend code inspects the `StrategySignal` model table indexes
- **THEN** indexes exist for querying by signal date and configuration version, and by status and generation timestamp

### Requirement: Strategy signal position ORM model
The system SHALL define a `StrategySignalPosition` SQLAlchemy ORM model for target position details produced by a strategy signal run.

#### Scenario: Model exposes signal position fields
- **WHEN** backend code inspects the `StrategySignalPosition` model table
- **THEN** the table includes columns for `id`, `strategy_signal_id`, `etf_id`, `rank`, `score`, `target_weight`, and `created_at`

#### Scenario: Signal position references signal run
- **WHEN** backend code inspects the `StrategySignalPosition` model table
- **THEN** `strategy_signal_id` references the `StrategySignal` table primary key

#### Scenario: Signal position references ETF metadata
- **WHEN** backend code inspects the `StrategySignalPosition` model table
- **THEN** `etf_id` references the `ETFInfo` table primary key

#### Scenario: Optional explanation fields
- **WHEN** backend code inspects the `StrategySignalPosition` model table
- **THEN** `rank` and `score` are nullable

### Requirement: Strategy signal position identity
The system SHALL prevent duplicate ETF position rows within the same strategy signal run.

#### Scenario: Same signal and same ETF
- **WHEN** two signal position rows use the same `strategy_signal_id` and `etf_id` values
- **THEN** the database rejects the duplicate row

#### Scenario: Same ETF in different signal runs
- **WHEN** two signal position rows use different `strategy_signal_id` values with the same `etf_id`
- **THEN** the database allows both rows

#### Scenario: Same rank in one signal run
- **WHEN** two signal position rows use the same `strategy_signal_id` and `rank` values
- **THEN** the database allows both rows

#### Scenario: Inspect signal position indexes
- **WHEN** backend code inspects the `StrategySignalPosition` model table indexes
- **THEN** an index exists for querying positions by strategy signal

### Requirement: Strategy signal migration metadata
The system SHALL expose ORM metadata that includes the strategy signal models to Alembic migration autogeneration.

#### Scenario: Alembic target metadata includes strategy signal tables
- **WHEN** Alembic loads the project model metadata
- **THEN** the metadata includes the `strategy_signal` and `strategy_signal_position` tables

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

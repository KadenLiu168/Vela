# strategy-signal-model Specification

## Purpose

Define the strategy signal persistence contract used by strategy generation and historical backtesting.
## Requirements
### Requirement: Strategy signal ORM model
The system SHALL define a `StrategySignal` SQLAlchemy ORM model for one strategy signal generation run.

#### Scenario: Model exposes signal run fields
- **WHEN** backend code inspects the `StrategySignal` model table
- **THEN** the table includes columns for `id`, `signal_date`, `strategy_id`, `config_version`, `generated_at`, `status`, `result`, `error_message`, `created_at`, and `updated_at`

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
- **WHEN** backend code persists a successful signal for a strategy id, signal date, config version, generated timestamp, result, and target positions
- **THEN** the database contains one `StrategySignal` row with those signal fields including `strategy_id`
- **AND** the database contains one `StrategySignalPosition` row for each target position

#### Scenario: Persist signal without positions
- **WHEN** backend code persists a signal result that has no target positions
- **THEN** the database contains the `StrategySignal` row and no child position rows for that signal

### Requirement: Strategy signal rerun persistence
The system SHALL preserve repeated generation for the same `signal_date` and `config_version` by creating a new strategy signal run instead of replacing prior runs.

#### Scenario: Same date and config version persisted twice
- **WHEN** backend code persists two signals with the same `signal_date` and `config_version`
- **THEN** the database contains two distinct `StrategySignal` rows

### Requirement: Latest successful strategy signal query
The system SHALL provide a core query helper that returns the latest successful strategy signal
for a `strategy_id`, `signal_date`, and `config_version` with its positions available.

#### Scenario: Latest successful signal exists
- **WHEN** backend code queries for a strategy id, date, and config version that have multiple
  successful strategy signal runs
- **THEN** the helper returns the matching successful run with the newest `generated_at` timestamp
  and id tie-breaker
- **AND** it ignores runs belonging to other strategies or config versions

#### Scenario: Latest successful signal ignores non-success rows
- **WHEN** backend code queries for a strategy id, date, and config version where a newer
  non-success run exists after an older successful run
- **THEN** the helper returns the older matching successful run

#### Scenario: Latest successful signal does not exist
- **WHEN** backend code queries for a strategy id, date, and config version that have no matching
  successful strategy signal run
- **THEN** the helper returns no signal

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

### Requirement: Strategy signal history list query
The system SHALL provide a core query helper that returns successful strategy signal summary rows for a given `strategy_id` and `config_version`, ordered newest-first, with limit and offset paging.

#### Scenario: List returns only successful signals for the strategy and version
- **WHEN** backend code queries with a `strategy_id` and `config_version` that have success, failed, and partial runs
- **THEN** the helper returns only the `success` runs

#### Scenario: List orders newest generation first
- **WHEN** backend code queries with multiple successful runs
- **THEN** the helper returns rows ordered by `generated_at` descending, then `id` descending

#### Scenario: List honors limit and offset
- **WHEN** backend code queries with `limit` and `offset`
- **THEN** the helper returns at most `limit` rows starting at `offset`

#### Scenario: List with no matches returns empty
- **WHEN** backend code queries with a `strategy_id` and `config_version` that have no successful run
- **THEN** the helper returns an empty list

### Requirement: Strategy signal by-id query
The system SHALL provide a core query helper that returns a full strategy signal report (with positions and ETF metadata) for a given signal id, without filtering by strategy.

#### Scenario: Signal id exists
- **WHEN** backend code queries with an existing signal id
- **THEN** the helper returns a report containing signal metadata and sorted target positions

#### Scenario: Signal id does not exist
- **WHEN** backend code queries with a signal id that no row has
- **THEN** the helper returns no report

#### Scenario: By-id query ignores strategy
- **WHEN** backend code queries with a signal id whose `strategy_id` differs from the current config
- **THEN** the helper still returns that signal's report

### Requirement: Strategy signal carries provenance

The `strategy_signal` table SHALL store a `source` discriminator and a nullable `backtest_run_id` foreign key on every signal row, so that live-generated signals and backtest-generated signals are distinguishable and linkable.

#### Scenario: source discriminator is required and constrained
- **WHEN** any code persists a strategy signal after this change
- **THEN** the row's `source` value is one of `manual`, `scheduled`, `backtest`, or `legacy`
- **AND** `source` is non-null
- **AND** a named database check constraint rejects any other stored value
- **AND** `legacy` is reserved for rows backfilled by the migration and is never an accepted input value on the generate endpoint

#### Scenario: backtest signals link to their run
- **WHEN** a strategy signal is produced by a backtest run
- **THEN** its `backtest_run_id` equals the producing `backtest_run.id`
- **AND** the `backtest_run` row exposes the signal through its `signals` relationship

#### Scenario: live signals have no backtest link
- **WHEN** a strategy signal is produced by live generation (manual or scheduled)
- **THEN** its `backtest_run_id` is null
- **AND** runtime validation and a named database check reject a manual or scheduled row with a non-null `backtest_run_id`

#### Scenario: legacy rows are explicitly marked
- **WHEN** a strategy signal row existed before provenance tracking was introduced
- **THEN** its `source` is `legacy`
- **AND** its `backtest_run_id` is null

#### Scenario: backtest link is indexed
- **WHEN** backend code inspects the `StrategySignal` model table indexes
- **THEN** an index exists on `backtest_run_id` for loading a run's signals
- **AND** no standalone `source` index is required until a source-filtering query is introduced

#### Scenario: runtime persistence rejects migration-only and unknown sources
- **WHEN** runtime code calls `persist_strategy_signal` with `source="legacy"` or an unknown value
- **THEN** the helper raises before adding a signal row


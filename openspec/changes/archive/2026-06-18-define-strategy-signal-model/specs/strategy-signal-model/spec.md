## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Strategy signal persistence helper
The system SHALL provide a core helper that persists one `StrategySignal` row and its associated `StrategySignalPosition` rows in the same SQLAlchemy session.

#### Scenario: Persist signal with positions
- **WHEN** backend code persists a successful signal for a strategy id, signal date, config version, generated timestamp, result, and target positions
- **THEN** the database contains one `StrategySignal` row with those signal fields including `strategy_id`
- **AND** the database contains one `StrategySignalPosition` row for each target position

#### Scenario: Persist signal without positions
- **WHEN** backend code persists a signal result that has no target positions
- **THEN** the database contains the `StrategySignal` row and no child position rows for that signal

## ADDED Requirements

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

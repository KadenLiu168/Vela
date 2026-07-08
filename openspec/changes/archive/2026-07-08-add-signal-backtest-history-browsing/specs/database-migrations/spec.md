## ADDED Requirements

### Requirement: Strategy signal strategy_id column and backtest rename migration
The system SHALL provide a single Alembic revision that adds a non-null `strategy_id` column to `strategy_signal` (backfilling every existing row with the current strategy config's `strategy_id`), renames `backtest_run.strategy_name` to `strategy_id`, and normalizes the renamed column's values to the current strategy config's `strategy_id`.

#### Scenario: Fresh database upgrades to head
- **WHEN** a developer runs `alembic upgrade head` against an empty SQLite database
- **THEN** the `strategy_signal` table includes a non-null `strategy_id` column
- **AND** the `backtest_run` table has a `strategy_id` column and no `strategy_name` column

#### Scenario: Existing signal rows are backfilled
- **WHEN** the revision is applied to a database with existing `strategy_signal` rows
- **THEN** every pre-existing row's `strategy_id` equals the current strategy config's `strategy_id`

#### Scenario: Backtest column is renamed and values normalized
- **WHEN** the revision is applied to a database whose `backtest_run.strategy_name` contains lowercase, mixed-case, or canonical values
- **THEN** the column is renamed to `strategy_id`
- **AND** every row's `strategy_id` equals the current strategy config's `strategy_id`

#### Scenario: Backtest strategy index remains usable
- **WHEN** the revision completes
- **THEN** an index on `backtest_run(strategy_id, config_version)` exists for strategy-scoped queries

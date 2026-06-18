# backtest-run-model Specification

## Purpose
Define the backtest run persistence contract used by historical backtesting and later result analysis.
## Requirements
### Requirement: Backtest run ORM model
The system SHALL define a `BacktestRun` SQLAlchemy ORM model for one historical backtest execution.

#### Scenario: Model exposes backtest run fields
- **WHEN** backend code inspects the `BacktestRun` model table
- **THEN** the table includes columns for `id`, `strategy_name`, `config_version`, `start_date`, `end_date`, `parameters_json`, `started_at`, `finished_at`, `status`, `error_message`, `total_return`, `annualized_return`, `max_drawdown`, `sharpe_ratio`, `volatility`, `created_at`, and `updated_at`

#### Scenario: Backtest run status values
- **WHEN** backend code creates backtest run rows for execution lifecycle states
- **THEN** the model supports `running`, `success`, `failed`, and `partial` status values

#### Scenario: Optional run completion fields
- **WHEN** backend code inspects the `BacktestRun` model table
- **THEN** `finished_at`, `error_message`, `total_return`, `annualized_return`, `max_drawdown`, `sharpe_ratio`, and `volatility` are nullable

### Requirement: Backtest run history
The system SHALL preserve multiple backtest runs for the same strategy name, configuration version, and date range.

#### Scenario: Same strategy config and date range rerun
- **WHEN** two backtest run rows use the same `strategy_name`, `config_version`, `start_date`, and `end_date` values
- **THEN** the database allows both rows

#### Scenario: Inspect backtest run indexes
- **WHEN** backend code inspects the `BacktestRun` model table indexes
- **THEN** indexes exist for querying by strategy name and configuration version, by status and start timestamp, and by requested start and end date

### Requirement: Backtest parameter snapshot
The system SHALL store the backtest parameter snapshot used for a run.

#### Scenario: Store serialized parameters
- **WHEN** backend code creates a backtest run row with serialized parameter data
- **THEN** the model can store the parameter data in `parameters_json`

### Requirement: Backtest equity point ORM model
The system SHALL define a `BacktestEquityPoint` SQLAlchemy ORM model for net value points produced by a backtest run.

#### Scenario: Model exposes equity point fields
- **WHEN** backend code inspects the `BacktestEquityPoint` model table
- **THEN** the table includes columns for `id`, `backtest_run_id`, `trade_date`, `net_value`, and `created_at`

#### Scenario: Equity point references backtest run
- **WHEN** backend code inspects the `BacktestEquityPoint` model table
- **THEN** `backtest_run_id` references the `BacktestRun` table primary key

#### Scenario: Equity point relationship exposes run data
- **WHEN** backend code loads a backtest run with related equity points
- **THEN** the ORM exposes the curve through `BacktestRun.equity_points` and the parent run through `BacktestEquityPoint.backtest_run`

### Requirement: Backtest equity point identity
The system SHALL prevent duplicate net value points within the same backtest run and trading date.

#### Scenario: Same run and same trading date
- **WHEN** two equity point rows use the same `backtest_run_id` and `trade_date` values
- **THEN** the database rejects the duplicate row

#### Scenario: Same trading date in different backtest runs
- **WHEN** two equity point rows use different `backtest_run_id` values with the same `trade_date`
- **THEN** the database allows both rows

#### Scenario: Inspect equity point indexes
- **WHEN** backend code inspects the `BacktestEquityPoint` model table indexes
- **THEN** an index exists for querying equity points by backtest run and trading date

### Requirement: Backtest run migration metadata
The system SHALL expose ORM metadata that includes the backtest run models to Alembic migration autogeneration.

#### Scenario: Alembic target metadata includes backtest tables
- **WHEN** Alembic loads the project model metadata
- **THEN** the metadata includes the `backtest_run` and `backtest_equity_point` tables

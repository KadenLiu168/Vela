## ADDED Requirements

### Requirement: Backtest equity curve ORM model
The system SHALL define a `BacktestEquityCurve` SQLAlchemy ORM model for daily net value and portfolio snapshot rows produced by a backtest run.

#### Scenario: Model exposes equity curve fields
- **WHEN** backend code inspects the `BacktestEquityCurve` model table
- **THEN** the table includes columns for `id`, `backtest_run_id`, `trade_date`, `net_value`, `cash`, `market_value`, `total_assets`, `positions_json`, and `created_at`

#### Scenario: Equity curve references backtest run
- **WHEN** backend code inspects the `BacktestEquityCurve` model table
- **THEN** `backtest_run_id` references the `BacktestRun` table primary key

#### Scenario: Equity curve relationship exposes run data
- **WHEN** backend code loads a backtest run with related equity curve rows
- **THEN** the ORM exposes the curve through `BacktestRun.equity_curve` and the parent run through `BacktestEquityCurve.backtest_run`

### Requirement: Backtest equity curve identity
The system SHALL prevent duplicate equity curve rows within the same backtest run and trading date.

#### Scenario: Same run and same trading date
- **WHEN** two equity curve rows use the same `backtest_run_id` and `trade_date` values
- **THEN** the database rejects the duplicate row

#### Scenario: Same trading date in different backtest runs
- **WHEN** two equity curve rows use different `backtest_run_id` values with the same `trade_date`
- **THEN** the database allows both rows

#### Scenario: Inspect equity curve indexes
- **WHEN** backend code inspects the `BacktestEquityCurve` model table indexes
- **THEN** an index exists for querying equity curve rows by backtest run and trading date

## MODIFIED Requirements

### Requirement: Backtest run migration metadata
The system SHALL expose ORM metadata that includes the backtest run models to Alembic migration autogeneration.

#### Scenario: Alembic target metadata includes backtest tables
- **WHEN** Alembic loads the project model metadata
- **THEN** the metadata includes the `backtest_run` and `backtest_equity_curve` tables
- **AND** the metadata does not include the `backtest_equity_point` table

## REMOVED Requirements

### Requirement: Backtest equity point ORM model
**Reason**: `BacktestEquityPoint` only records a daily net value point and is replaced by the wider `BacktestEquityCurve` daily portfolio snapshot model.

**Migration**: Use `BacktestEquityCurve` and `BacktestRun.equity_curve` for daily backtest curve rows.

### Requirement: Backtest equity point identity
**Reason**: Duplicate protection now belongs to `BacktestEquityCurve` rows.

**Migration**: Use the `BacktestEquityCurve` unique constraint on `backtest_run_id` and `trade_date`.

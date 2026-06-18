# etf-info-model Specification

## Purpose

Define the ETF metadata identity and lookup contract used by market data, strategy signals, and historical backtesting.

## Requirements

### Requirement: ETF ORM model
The system SHALL define an `ETFInfo` SQLAlchemy ORM model for ETF metadata.

#### Scenario: Model exposes ETF metadata fields
- **WHEN** backend code inspects the `ETFInfo` model table
- **THEN** the table includes columns for `id`, `exchange`, `symbol`, `name`, `currency`, `issuer`, `category`, `inception_date`, `expense_ratio`, `is_active`, `created_at`, and `updated_at`

### Requirement: International ETF identity
The system SHALL enforce ETF identity uniqueness by the combination of `exchange` and `symbol`.

#### Scenario: Same symbol on different exchanges
- **WHEN** two ETF metadata rows use the same `symbol` with different `exchange` values
- **THEN** the database allows both rows

#### Scenario: Duplicate symbol on same exchange
- **WHEN** two ETF metadata rows use the same `exchange` and `symbol` values
- **THEN** the database rejects the duplicate row

### Requirement: ETF lookup indexes
The system SHALL define indexes that support ETF metadata lookup by symbol, exchange, and active status.

#### Scenario: Inspect ETF indexes
- **WHEN** backend code inspects the `ETFInfo` model table indexes
- **THEN** indexes exist for `symbol`, `exchange`, and `is_active`

### Requirement: Alembic metadata discovery
The system SHALL expose ORM metadata that includes `ETFInfo` to Alembic migration autogeneration.

#### Scenario: Alembic target metadata includes ETF table
- **WHEN** Alembic imports the migration environment target metadata
- **THEN** the target metadata includes the ETF metadata table

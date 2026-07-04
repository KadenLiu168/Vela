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

### Requirement: ETF metadata synchronization from configured pool
The system SHALL synchronize validated ETF pool entries into persisted `ETFInfo` rows.

#### Scenario: Insert configured ETF metadata
- **WHEN** ETF pool synchronization runs against a database missing a configured `(exchange, symbol)` row
- **THEN** the system inserts an `ETFInfo` row for that configured ETF

#### Scenario: Update configured ETF metadata
- **WHEN** ETF pool synchronization runs and a configured `(exchange, symbol)` row already exists with different YAML-owned metadata
- **THEN** the system updates the persisted `name`, `currency`, `category`, and `is_active` values from the ETF pool entry

#### Scenario: Keep synchronization idempotent
- **WHEN** ETF pool synchronization runs more than once with unchanged ETF pool configuration
- **THEN** subsequent runs leave the existing ETF rows unchanged and report them as unchanged

#### Scenario: Preserve rows outside configured pool
- **WHEN** ETF pool synchronization runs and the database contains ETF rows not present in the configured pool
- **THEN** the system does not delete or automatically deactivate those rows


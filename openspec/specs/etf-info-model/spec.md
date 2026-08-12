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
The system SHALL synchronize validated ETF pool entries into persisted `ETFInfo` rows. Every active configured entry SHALL contain an ISO exchange `listing_date`; fund `inception_date` remains separately optional. Pool synchronization SHALL own `name`, `currency`, `category`, `is_active`, `inception_date`, and `listing_date` for entries present in that versioned pool without deleting rows outside it.

#### Scenario: Insert configured ETF metadata
- **WHEN** ETF pool synchronization runs against a database missing a configured `(exchange, symbol)` row
- **THEN** the system inserts an `ETFInfo` row with the configured identity, descriptive fields, fund inception date if supplied, listing date, and active state

#### Scenario: Update configured ETF metadata
- **WHEN** ETF pool synchronization runs and a configured `(exchange, symbol)` row already exists with different pool-owned metadata
- **THEN** the system updates the persisted `name`, `currency`, `category`, `is_active`, `inception_date`, and `listing_date` values from the ETF pool entry

#### Scenario: Keep synchronization idempotent
- **WHEN** ETF pool synchronization runs more than once with unchanged ETF pool configuration
- **THEN** subsequent runs leave the existing ETF rows unchanged and report them as unchanged

#### Scenario: Preserve rows outside configured pool
- **WHEN** ETF pool synchronization runs and the database contains ETF rows not present in the configured pool
- **THEN** the system does not delete or automatically deactivate those rows

#### Scenario: Reject active entry without listing date
- **WHEN** ETF pool configuration declares an active ETF without `listing_date`
- **THEN** configuration validation fails before synchronization writes any row

### Requirement: ETF listing eligibility metadata
The system SHALL store nullable fund `inception_date` and nullable exchange `listing_date` as distinct ETF metadata. Every active ETF supplied to historical strategy, benchmark, backtest, or Walk-forward execution MUST have a declared `listing_date`; local `first_stored_date` MUST NOT substitute for it.

#### Scenario: Fund inception predates exchange listing
- **WHEN** an ETF has different fund inception and exchange listing dates
- **THEN** both dates are preserved independently
- **AND** strategy eligibility begins on the exchange listing date

#### Scenario: Active ETF lacks listing date
- **WHEN** an active ETF without `listing_date` reaches research-input preflight
- **THEN** preflight fails with the ETF identity before strategy output

#### Scenario: First stored row does not define listing
- **WHEN** the first locally stored market row is later than the declared listing date
- **THEN** the system treats the intervening required sessions as unresolved input rather than pre-listing time


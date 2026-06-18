## ADDED Requirements

### Requirement: Market price ORM model
The system SHALL define a `MarketPrice` SQLAlchemy ORM model for ETF daily market prices.

#### Scenario: Model exposes ETF daily price fields
- **WHEN** backend code inspects the `MarketPrice` model table
- **THEN** the table includes columns for `id`, `etf_id`, `trade_date`, `open_price`, `high_price`, `low_price`, `close_price`, `adjusted_close`, `volume`, `created_at`, and `updated_at`

#### Scenario: Market price references ETF metadata
- **WHEN** backend code inspects the `MarketPrice` model table
- **THEN** `etf_id` references the `ETFInfo` table primary key

### Requirement: Market price daily identity
The system SHALL enforce market price identity by the combination of ETF and trading date.

#### Scenario: Same ETF and same trading date
- **WHEN** two market price rows use the same `etf_id` and `trade_date` values
- **THEN** the database rejects the duplicate row

#### Scenario: Different ETFs on same trading date
- **WHEN** two market price rows use different `etf_id` values with the same `trade_date`
- **THEN** the database allows both rows

#### Scenario: Upsert conflict target
- **WHEN** ingestion code needs to upsert daily market prices
- **THEN** the model provides a unique constraint on `etf_id` and `trade_date` as the conflict target

### Requirement: Market price query indexes
The system SHALL define indexes that support daily market price lookup for strategy and backtest calculations.

#### Scenario: Inspect market price indexes
- **WHEN** backend code inspects the `MarketPrice` model table indexes
- **THEN** indexes exist for querying prices by ETF over trading dates and by trading date

### Requirement: Strategy price selection
The system SHALL define the strategy calculation price as adjusted close when available, otherwise raw close.

#### Scenario: Adjusted close is available
- **WHEN** a market price row has a non-null `adjusted_close`
- **THEN** strategy calculations use `adjusted_close` as the price value

#### Scenario: Adjusted close is missing
- **WHEN** a market price row has a null `adjusted_close`
- **THEN** strategy calculations fall back to `close_price` as the price value

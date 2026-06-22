# market-data Specification

## Purpose

Define normalized market data storage and access behavior used by ETF strategy signals and historical backtesting.
## Requirements
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

### Requirement: Data fetch log ORM model
The system SHALL define a `DataFetchLog` SQLAlchemy ORM model for market data fetch task logging.

#### Scenario: Model exposes fetch task fields
- **WHEN** backend code inspects the `DataFetchLog` model table
- **THEN** the table includes columns for `id`, `source`, `target_type`, `fetch_mode`, `range_start`, `range_end`, `requested_symbols`, `started_at`, `finished_at`, `status`, `rows_fetched`, `rows_inserted`, `rows_updated`, `error_message`, `created_at`, and `updated_at`

#### Scenario: Optional task fields are nullable
- **WHEN** backend code inspects the `DataFetchLog` model table
- **THEN** `range_start`, `range_end`, `requested_symbols`, `finished_at`, `rows_fetched`, `rows_inserted`, `rows_updated`, and `error_message` are nullable

### Requirement: Data fetch task status tracking
The system SHALL allow fetch logs to record whether a market data fetch task is running, succeeded, failed, or partially completed.

#### Scenario: Inspect allowed fetch statuses
- **WHEN** backend code creates fetch log rows for task lifecycle states
- **THEN** the model supports `running`, `success`, `failed`, and `partial` status values

#### Scenario: Record failed fetch error
- **WHEN** a fetch task fails with an error message
- **THEN** the fetch log can store the failure status and error message for later investigation

#### Scenario: Record partial fetch result
- **WHEN** a fetch task completes for only part of the requested range or symbol universe
- **THEN** the fetch log can store the partial status, result counts, and error message for later investigation

### Requirement: Full and incremental fetch scope logging
The system SHALL record enough fetch scope information to distinguish and investigate full and incremental market data fetches.

#### Scenario: Record full fetch scope
- **WHEN** a full market data fetch task is logged
- **THEN** the fetch log records the source, target type, full fetch mode, requested date range, and requested symbols

#### Scenario: Record incremental fetch scope
- **WHEN** an incremental market data fetch task is logged
- **THEN** the fetch log records the source, target type, incremental fetch mode, requested date range, and requested symbols

### Requirement: Data fetch log query indexes
The system SHALL define indexes that support market data fetch troubleshooting by source, status, target, fetch mode, and time range.

#### Scenario: Inspect data fetch log indexes
- **WHEN** backend code inspects the `DataFetchLog` model table indexes
- **THEN** indexes exist for querying logs by source, status, and start time, and for querying logs by target type, fetch mode, and requested date range

### Requirement: Provider daily price to market price mapping
The system SHALL provide a tested mapping from normalized provider daily price values into internal `MarketPrice` fields.

#### Scenario: Map provider daily price fields
- **WHEN** backend code maps a provider daily price value with an internal ETF id
- **THEN** the resulting `MarketPrice` row uses that ETF id and preserves trade date, open price, high price, low price, close price, adjusted close, and volume values

#### Scenario: Preserve explicit field types
- **WHEN** backend code maps a provider daily price value into a `MarketPrice` row
- **THEN** trade date remains a date value, price fields remain decimal values, and volume remains an optional integer value

#### Scenario: Keep provider mapping independent from ETF lookup
- **WHEN** backend code maps a provider daily price value into a `MarketPrice` row
- **THEN** the mapper does not query ETF metadata or infer `etf_id` from the provider symbol


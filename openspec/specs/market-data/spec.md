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

### Requirement: Market price fetch workflow logging
The system SHALL write `DataFetchLog` rows when a market price fetch workflow runs for full or incremental ETF daily price data.

#### Scenario: Log successful full fetch
- **WHEN** a full market price fetch workflow successfully fetches and upserts ETF daily prices
- **THEN** the system records a `DataFetchLog` row with `fetch_mode` set to `full`, the requested date range, requested symbols, `success` status, fetched row count, inserted row count, updated row count, and finish time

#### Scenario: Log successful incremental fetch
- **WHEN** an incremental market price fetch workflow successfully fetches and upserts ETF daily prices
- **THEN** the system records a `DataFetchLog` row with `fetch_mode` set to `incremental`, the requested date range, requested symbols, `success` status, fetched row count, inserted row count, updated row count, and finish time

#### Scenario: Log failed fetch
- **WHEN** a market price fetch workflow cannot fetch or map any requested ETF daily prices
- **THEN** the system records a `DataFetchLog` row with `failed` status, finish time, and an error message describing the failure

#### Scenario: Log partial fetch
- **WHEN** a market price fetch workflow fetches and upserts at least one requested symbol but fails for another requested symbol
- **THEN** the system records a `DataFetchLog` row with `partial` status, successful result counts, finish time, and an error message identifying the failed symbol or symbols

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

### Requirement: Market price upsert persistence
The system SHALL provide SQLite upsert behavior for daily ETF market prices using ETF and trading date as the row identity.

#### Scenario: Insert new market price
- **WHEN** backend code upserts a market price whose `etf_id` and `trade_date` are not present in SQLite
- **THEN** the system inserts a new `market_price` row

#### Scenario: Prevent duplicate ETF trading date rows
- **WHEN** backend code upserts a market price with the same `etf_id` and `trade_date` as an existing row
- **THEN** the system keeps one row for that ETF and trading date

#### Scenario: Update existing market price
- **WHEN** backend code upserts a market price with the same `etf_id` and `trade_date` as an existing row but different price or volume fields
- **THEN** the system updates the existing row with the supplied market price fields

#### Scenario: Preserve different ETFs on same trading date
- **WHEN** backend code upserts market prices for different ETFs on the same trading date
- **THEN** the system stores one row per ETF

#### Scenario: Report upsert counts
- **WHEN** backend code upserts market prices
- **THEN** the system returns separate counts for inserted rows and updated rows

#### Scenario: Handle duplicate keys in one batch
- **WHEN** backend code upserts multiple market prices with the same `etf_id` and `trade_date` in one call
- **THEN** the system stores one row for that key using the last supplied market price values

### Requirement: Full active ETF market price fetch workflow
The system SHALL provide a full daily market price fetch workflow that processes all active ETF metadata rows.

#### Scenario: Fetch active ETF universe
- **WHEN** the full market price fetch workflow runs
- **THEN** the system fetches daily prices for ETF metadata rows where `is_active` is true

#### Scenario: Ignore inactive ETFs
- **WHEN** the full market price fetch workflow runs and inactive ETF metadata rows exist
- **THEN** the system does not request provider data for inactive ETF rows

#### Scenario: Empty active ETF universe
- **WHEN** the full market price fetch workflow runs and no active ETF rows exist
- **THEN** the system records a failed fetch result with an error message explaining that no active ETFs were found

### Requirement: Full market price fetch persistence
The system SHALL persist fetched full daily ETF market prices through the existing provider mapping and SQLite upsert behavior.

#### Scenario: Persist fetched daily prices
- **WHEN** the full market price fetch workflow receives provider daily price values for an active ETF
- **THEN** the system maps those values to `MarketPrice` rows using the ETF id and upserts them into SQLite

#### Scenario: Report persistence counts
- **WHEN** the full market price fetch workflow upserts fetched market prices
- **THEN** the system reports fetched row count, inserted row count, and updated row count

### Requirement: Full market price fetch logging
The system SHALL record one `DataFetchLog` row for each full daily market price fetch workflow run.

#### Scenario: Log successful full fetch
- **WHEN** the full market price fetch workflow fetches and persists all requested active ETFs successfully
- **THEN** the system records a fetch log with `fetch_mode` set to `full`, `target_type` set to `market_price`, requested symbols, `success` status, row counts, and finish time

#### Scenario: Log failed full fetch
- **WHEN** the full market price fetch workflow cannot fetch and persist any requested active ETF
- **THEN** the system records a fetch log with `failed` status, finish time, zero successful row counts, and an error message

#### Scenario: Log partial full fetch
- **WHEN** the full market price fetch workflow persists at least one active ETF and fails at least one other active ETF
- **THEN** the system records a fetch log with `partial` status, successful row counts, finish time, and an error message identifying failed symbols

### Requirement: Incremental active ETF market price fetch workflow
The system SHALL provide an incremental daily market price fetch workflow that processes all active ETF metadata rows for dates after the latest local market price date.

#### Scenario: Infer incremental date range from local market prices
- **WHEN** the incremental market price fetch workflow runs and local market prices exist
- **THEN** the system uses the maximum local `market_price.trade_date` plus one calendar day as the requested start date

#### Scenario: Fetch incremental prices for active ETF universe
- **WHEN** the incremental market price fetch workflow runs with a local market price baseline
- **THEN** the system fetches daily prices for ETF metadata rows where `is_active` is true using the inferred start date

#### Scenario: Ignore inactive ETFs
- **WHEN** the incremental market price fetch workflow runs and inactive ETF metadata rows exist
- **THEN** the system does not request provider data for inactive ETF rows

#### Scenario: Missing local market price baseline
- **WHEN** the incremental market price fetch workflow runs and no local market prices exist
- **THEN** the system records a failed fetch result with an error message explaining that no local market price baseline was found

### Requirement: Incremental market price fetch persistence
The system SHALL persist fetched incremental daily ETF market prices through the existing provider mapping and SQLite upsert behavior.

#### Scenario: Persist fetched incremental daily prices
- **WHEN** the incremental market price fetch workflow receives provider daily price values for an active ETF
- **THEN** the system maps those values to `MarketPrice` rows using the ETF id and upserts them into SQLite

#### Scenario: Prevent duplicate rows on repeated incremental runs
- **WHEN** the incremental market price fetch workflow receives daily prices whose ETF and trading date already exist in SQLite
- **THEN** the system keeps one market price row for that ETF and trading date

#### Scenario: Report incremental persistence counts
- **WHEN** the incremental market price fetch workflow upserts fetched market prices
- **THEN** the system reports fetched row count, inserted row count, and updated row count

### Requirement: Incremental market price fetch logging
The system SHALL record one `DataFetchLog` row for each incremental daily market price fetch workflow run.

#### Scenario: Log successful incremental fetch
- **WHEN** the incremental market price fetch workflow fetches and persists all requested active ETFs successfully
- **THEN** the system records a fetch log with `fetch_mode` set to `incremental`, `target_type` set to `market_price`, requested date range, requested symbols, `success` status, row counts, and finish time

#### Scenario: Log failed incremental fetch
- **WHEN** the incremental market price fetch workflow cannot fetch and persist any requested active ETF daily prices
- **THEN** the system records a fetch log with `failed` status, finish time, zero successful row counts, and an error message

#### Scenario: Log partial incremental fetch
- **WHEN** the incremental market price fetch workflow persists at least one active ETF and fails at least one other active ETF
- **THEN** the system records a fetch log with `partial` status, successful row counts, finish time, and an error message identifying failed symbols


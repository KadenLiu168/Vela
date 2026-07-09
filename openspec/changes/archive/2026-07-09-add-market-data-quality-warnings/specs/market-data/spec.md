## MODIFIED Requirements

### Requirement: Data fetch log ORM model
The system SHALL define a `DataFetchLog` SQLAlchemy ORM model for market data fetch task logging.

#### Scenario: Model exposes fetch task fields
- **WHEN** backend code inspects the `DataFetchLog` model table
- **THEN** the table includes columns for `id`, `source`, `target_type`, `fetch_mode`, `range_start`, `range_end`, `requested_symbols`, `started_at`, `finished_at`, `status`, `rows_fetched`, `rows_inserted`, `rows_updated`, `error_message`, `quality_warnings`, `created_at`, and `updated_at`

#### Scenario: Optional task fields are nullable
- **WHEN** backend code inspects the `DataFetchLog` model table
- **THEN** `range_start`, `range_end`, `requested_symbols`, `finished_at`, `rows_fetched`, `rows_inserted`, `rows_updated`, `error_message`, and `quality_warnings` are nullable

## ADDED Requirements

### Requirement: Duplicate trade date detection
The system SHALL detect duplicate `(etf_id, trade_date)` keys within a single market price fetch batch before upsert and record them as quality warnings, without changing the existing last-write-wins deduplication semantics.

#### Scenario: Detect duplicate trade dates in a fetch batch
- **WHEN** a market price fetch batch contains more than one `MarketPrice` row for the same `etf_id` and `trade_date`
- **THEN** the system detects the duplicate keys before upsert
- **AND** records a quality warning identifying each duplicate `etf_id`, `trade_date`, and the number of collapsed rows
- **AND** persists the warnings as JSON in the `DataFetchLog.quality_warnings` column

#### Scenario: No duplicates yields no warnings
- **WHEN** a market price fetch batch contains no duplicate `(etf_id, trade_date)` keys
- **THEN** the `DataFetchLog.quality_warnings` value is null

#### Scenario: Warnings do not change deduplication behavior
- **WHEN** duplicate trade dates are detected in a fetch batch
- **THEN** the system still upserts using the existing last-write-wins semantics that keep the last supplied values for each key
- **AND** the quality warning is an observable soft signal that does not block the upsert

#### Scenario: Warnings are readable from the fetch result
- **WHEN** a market price fetch workflow completes with detected duplicate trade dates
- **THEN** the returned `MarketDataFetchResult` exposes the quality warnings
- **AND** the persisted `DataFetchLog` row stores the quality warnings

#### Scenario: Duplicate detection is a pure function
- **WHEN** backend code invokes the duplicate trade date detector
- **THEN** the detector is a pure function that accepts a sequence of market prices and returns the duplicate keys without holding a database session or mutating its inputs

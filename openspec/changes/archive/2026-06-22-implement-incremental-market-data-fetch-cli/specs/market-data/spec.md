## ADDED Requirements

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

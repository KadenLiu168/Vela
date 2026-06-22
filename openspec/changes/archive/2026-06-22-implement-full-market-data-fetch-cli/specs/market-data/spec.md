## ADDED Requirements

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

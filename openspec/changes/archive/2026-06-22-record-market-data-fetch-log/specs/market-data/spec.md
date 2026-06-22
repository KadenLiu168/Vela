## ADDED Requirements

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

# market-price-panel-loading Specification

## Purpose
Defines the canonical one-shot multi-ETF market price panel loader (`load_price_panel`) that fetches a date-range panel in a single query, grouped by ETF id.
## Requirements
### Requirement: Multi-ETF market price panel loading

The system SHALL provide a public function that loads daily market prices for a list of ETF ids over a closed date range in a single database query, returning the prices grouped by ETF id in ascending trade-date order.

> Cross-reference: this capability owns the canonical one-shot loader (`load_price_panel`) contract. The `market-data` capability also describes this loader from the caller-guidance angle. Both MUST stay in sync — edit them together.

#### Scenario: Load panel for a list of ETFs over a date range
- **WHEN** backend code calls the panel loader with a non-empty ETF id list and a start date and end date
- **THEN** the function performs exactly one `SELECT` against the `market_price` table whose `WHERE` clause filters on `etf_id IN (...)` AND `trade_date BETWEEN start_date AND end_date`
- **AND** the returned value is a mapping from each requested ETF id to a list of `MarketPrice` rows sorted by `trade_date` ascending

#### Scenario: Panel excludes ETFs without any market price rows
- **WHEN** backend code calls the panel loader with an ETF id list and the database contains zero `MarketPrice` rows for some requested ETF id in the date range
- **THEN** the returned mapping contains no entry for that ETF id

#### Scenario: Panel includes every requested trading-date row
- **WHEN** backend code calls the panel loader for an ETF id and the database contains N `MarketPrice` rows in the requested date range
- **THEN** the returned list for that ETF id contains exactly N rows
- **AND** the first row's `trade_date` is the earliest requested-date row and the last row's `trade_date` equals the requested end date when a row exists for that date

#### Scenario: Panel reuses the etf-and-trade-date composite index
- **WHEN** backend code calls the panel loader
- **THEN** the generated SQL does not introduce additional indexes or tables beyond the existing `ix_market_price_etf_trade_date` index on `(etf_id, trade_date)`

#### Scenario: Empty ETF id list returns empty panel
- **WHEN** backend code calls the panel loader with an empty ETF id list
- **THEN** the returned mapping is empty
- **AND** the function does not raise

#### Scenario: Caller owns panel lifecycle
- **WHEN** backend code receives a panel mapping from the loader
- **THEN** the loader does not cache the panel internally


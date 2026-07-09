## MODIFIED Requirements

### Requirement: Multi-ETF market price panel loading

The system SHALL provide a public function that loads daily market prices for a list of ETF ids over a closed date range in a single database query, returning the prices grouped by ETF id in ascending trade-date order. The function is the recommended one-shot primitive for any caller that needs historical prices across multiple ETFs.

> Cross-reference: the canonical one-shot loader (`load_price_panel`) is specified jointly with the `market-price-panel-loading` capability. That capability owns the full contract (caller-owned lifecycle, trading-date row inclusion, composite-index reuse); this capability focuses on the recommended-caller guidance. Both MUST stay in sync — edit them together.

#### Scenario: Load panel for a list of ETFs over a date range
- **WHEN** backend code calls the panel loader with a non-empty ETF id list and a start date and end date
- **THEN** the function performs exactly one `SELECT` against the `market_price` table whose `WHERE` clause filters on `etf_id IN (...)` AND `trade_date BETWEEN start_date AND end_date`
- **AND** the returned value is a mapping from each requested ETF id to a list of `MarketPrice` rows sorted by `trade_date` ascending

#### Scenario: Panel excludes ETFs without any market price rows
- **WHEN** backend code calls the panel loader with an ETF id list and the database contains zero `MarketPrice` rows for some requested ETF id in the date range
- **THEN** the returned mapping contains no entry for that ETF id

#### Scenario: Panel reuses the etf-and-trade-date composite index
- **WHEN** backend code calls the panel loader
- **THEN** the generated SQL does not introduce additional indexes or tables beyond the existing `ix_market_price_etf_trade_date` index on `(etf_id, trade_date)`

#### Scenario: Empty ETF id list returns empty panel
- **WHEN** backend code calls the panel loader with an empty ETF id list
- **THEN** the returned mapping is empty
- **AND** the function does not raise

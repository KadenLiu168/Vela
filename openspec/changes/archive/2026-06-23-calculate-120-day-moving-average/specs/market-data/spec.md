## ADDED Requirements

### Requirement: Market price 120-day moving average calculation
The system SHALL calculate a 120-trading-day moving average for a single ETF from stored `MarketPrice` history.

#### Scenario: Calculate complete 120-day moving average
- **WHEN** backend code calculates the 120-day moving average for an ETF and `as_of_date` with 120 same-ETF `MarketPrice` rows through that date
- **THEN** the system returns the arithmetic average of those 120 strategy prices for that ETF

#### Scenario: Use strategy price for moving average calculation
- **WHEN** a `MarketPrice` row has a non-null `adjusted_close`
- **THEN** the moving average calculation uses `adjusted_close` for that row
- **AND** when `adjusted_close` is null, the calculation uses `close_price`

#### Scenario: Count moving average window by trading price rows
- **WHEN** backend code calculates the 120-day moving average for an ETF and `as_of_date`
- **THEN** the moving average window includes the `as_of_date` row and the 119 earlier `MarketPrice` rows for the same ETF ordered by `trade_date`

#### Scenario: Missing historical data returns null moving average
- **WHEN** backend code calculates the 120-day moving average for an ETF with fewer than 120 same-ETF `MarketPrice` rows through `as_of_date`
- **THEN** the moving average value is null

#### Scenario: Missing current price returns null moving average
- **WHEN** backend code calculates the 120-day moving average for an ETF and no `MarketPrice` exists for the requested `as_of_date`
- **THEN** the moving average value is null

#### Scenario: Isolate ETF histories
- **WHEN** market prices exist for multiple ETFs
- **THEN** the moving average calculation only uses `MarketPrice` rows for the requested ETF

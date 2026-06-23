## ADDED Requirements

### Requirement: Market price window return calculation
The system SHALL calculate 20 / 60 / 120 trading-day returns for a single ETF from stored `MarketPrice` history.

#### Scenario: Calculate complete window returns
- **WHEN** backend code calculates market price returns for an ETF and `as_of_date` with enough prior trading-day `MarketPrice` rows
- **THEN** the system returns 20-day, 60-day, and 120-day returns for that ETF
- **AND** each return uses the formula `current strategy price / prior strategy price - 1`

#### Scenario: Use strategy price for return calculation
- **WHEN** a `MarketPrice` row has a non-null `adjusted_close`
- **THEN** the return calculation uses `adjusted_close` for that row
- **AND** when `adjusted_close` is null, the calculation uses `close_price`

#### Scenario: Count windows by trading price rows
- **WHEN** backend code calculates a 20-day return
- **THEN** the prior price is the 20th earlier `MarketPrice` row for the same ETF ordered by `trade_date`
- **AND** the same trading-row counting rule applies to 60-day and 120-day returns

#### Scenario: Missing historical data returns null windows
- **WHEN** backend code calculates market price returns for an ETF whose history is insufficient for one or more windows
- **THEN** each insufficient window return is null
- **AND** windows with enough history still return calculated values

#### Scenario: Missing current price returns null windows
- **WHEN** backend code calculates market price returns for an ETF and no `MarketPrice` exists for the requested `as_of_date`
- **THEN** the 20-day, 60-day, and 120-day returns are null

#### Scenario: Isolate ETF histories
- **WHEN** market prices exist for multiple ETFs
- **THEN** the return calculation only uses `MarketPrice` rows for the requested ETF

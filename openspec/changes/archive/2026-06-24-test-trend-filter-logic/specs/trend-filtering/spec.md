## MODIFIED Requirements

### Requirement: ETF trend filter calculation
The system SHALL apply a configured trend filter for one ETF using current strategy price and a 120-trading-day moving average.

#### Scenario: Pass trend filter when price is above moving average
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` where the current strategy price is greater than the 120-day moving average
- **THEN** the system returns the current strategy price
- **AND** the system returns the 120-day moving average
- **AND** the ETF passes the trend filter

#### Scenario: Fail trend filter when price equals moving average
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` where the current strategy price equals the 120-day moving average
- **THEN** the ETF does not pass the trend filter

#### Scenario: Fail trend filter when price is below moving average
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` where the current strategy price is less than the 120-day moving average
- **THEN** the ETF does not pass the trend filter

#### Scenario: Mixed ETF filter outcomes
- **WHEN** backend code applies the trend filter to multiple ETFs for the same `as_of_date`, and at least one ETF's current strategy price is above its 120-day moving average while another ETF's current strategy price is not above its 120-day moving average
- **THEN** only the ETF whose current strategy price is above its 120-day moving average passes the trend filter
- **AND** the ETF whose current strategy price is not above its 120-day moving average does not pass the trend filter

#### Scenario: Missing current price fails trend filter
- **WHEN** backend code applies the trend filter for an ETF and no `MarketPrice` exists for the requested ETF on the requested `as_of_date`
- **THEN** the current strategy price is null
- **AND** the ETF does not pass the trend filter

#### Scenario: Missing moving average fails trend filter
- **WHEN** backend code applies the trend filter for an ETF with fewer than 120 same-ETF `MarketPrice` rows through `as_of_date`
- **THEN** the 120-day moving average is null
- **AND** the ETF does not pass the trend filter

#### Scenario: Isolate ETF histories
- **WHEN** backend code applies the trend filter and market prices exist for multiple ETFs
- **THEN** the current strategy price and moving average use only `MarketPrice` rows for the requested ETF

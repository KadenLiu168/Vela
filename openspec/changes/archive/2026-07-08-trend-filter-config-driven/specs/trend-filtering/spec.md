## MODIFIED Requirements

### Requirement: ETF trend filter calculation
The system SHALL apply a configured trend filter for one ETF using the current strategy price, a moving average over the configured `moving_average_days` window (one of 60, 120, or 250 trading days), and the configured `price_relation` (`above` or `below`). The filter passes only when the current strategy price satisfies the configured relation against the moving average using strict comparison (`>` for `above`, `<` for `below`); equality does not pass.

#### Scenario: Pass trend filter when price is above moving average with above relation
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` with `price_relation` set to `above` and the current strategy price is greater than the configured-window moving average
- **THEN** the system returns the current strategy price
- **AND** the system returns the configured-window moving average
- **AND** the ETF passes the trend filter

#### Scenario: Fail trend filter when price equals moving average
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` where the current strategy price equals the configured-window moving average
- **THEN** the ETF does not pass the trend filter

#### Scenario: Fail trend filter when price is above moving average but relation is below
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` with `price_relation` set to `below` and the current strategy price is greater than the configured-window moving average
- **THEN** the ETF does not pass the trend filter

#### Scenario: Pass trend filter when price is below moving average with below relation
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` with `price_relation` set to `below` and the current strategy price is less than the configured-window moving average
- **THEN** the system returns the current strategy price
- **AND** the system returns the configured-window moving average
- **AND** the ETF passes the trend filter

#### Scenario: Configured window drives the moving average window
- **WHEN** backend code applies the trend filter for an ETF and `as_of_date` with `moving_average_days` set to `60` and at least 60 same-ETF `MarketPrice` rows exist through `as_of_date`
- **THEN** the moving average is computed over exactly the 60 most recent same-ETF `MarketPrice` rows
- **AND** any same-ETF `MarketPrice` row older than the 60-row window does not affect the moving average

#### Scenario: Mixed ETF filter outcomes
- **WHEN** backend code applies the trend filter to multiple ETFs for the same `as_of_date`, and at least one ETF's current strategy price satisfies its configured relation while another ETF's current strategy price does not
- **THEN** only the ETF whose current strategy price satisfies its configured relation passes the trend filter
- **AND** the ETF whose current strategy price does not satisfy its configured relation does not pass the trend filter

#### Scenario: Missing current price fails trend filter
- **WHEN** backend code applies the trend filter for an ETF and no `MarketPrice` exists for the requested ETF on the requested `as_of_date`
- **THEN** the current strategy price is null
- **AND** the ETF does not pass the trend filter

#### Scenario: Missing moving average fails trend filter
- **WHEN** backend code applies the trend filter for an ETF with fewer than `moving_average_days` same-ETF `MarketPrice` rows through `as_of_date`
- **THEN** the moving average is null
- **AND** the ETF does not pass the trend filter

#### Scenario: Isolate ETF histories
- **WHEN** backend code applies the trend filter and market prices exist for multiple ETFs
- **THEN** the current strategy price and moving average use only `MarketPrice` rows for the requested ETF

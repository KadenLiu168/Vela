## ADDED Requirements

### Requirement: AkShare ETF daily price provider
The system SHALL provide an AkShare-backed market data provider for fetching ETF daily market prices.

#### Scenario: Fetch ETF daily prices through AkShare
- **WHEN** backend code requests ETF daily prices from the AkShare market data provider
- **THEN** the provider fetches daily ETF行情 through AkShare `fund_etf_hist_em`

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code supplies optional start and end dates to the AkShare market data provider
- **THEN** the provider sends those bounds to AkShare using `YYYYMMDD` date strings

#### Scenario: Use unadjusted daily prices by default
- **WHEN** the AkShare market data provider requests ETF daily prices
- **THEN** it requests unadjusted AkShare data and leaves `adjusted_close` unset in returned daily price values

### Requirement: AkShare daily price normalization
The system SHALL normalize AkShare ETF daily rows into the internal provider daily price contract.

#### Scenario: Normalize AkShare ETF OHLCV fields
- **WHEN** AkShare returns ETF daily rows with date, open, high, low, close, and volume columns
- **THEN** the provider returns `DailyPrice` values with symbol, trade date, open price, high price, low price, close price, optional adjusted close, and optional volume fields

#### Scenario: Hide AkShare table shape from callers
- **WHEN** backend code receives values from the AkShare market data provider
- **THEN** it does not need to inspect pandas DataFrames or AkShare-specific column names

#### Scenario: Empty AkShare result
- **WHEN** AkShare returns no ETF daily rows for the requested symbol and date range
- **THEN** the provider returns an empty sequence

### Requirement: AkShare provider error propagation
The system SHALL expose AkShare provider failures as catchable provider-level errors.

#### Scenario: AkShare source call fails
- **WHEN** AkShare raises an error while fetching ETF daily prices
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: AkShare row normalization fails
- **WHEN** AkShare returns rows that cannot be normalized into the internal daily price contract
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: Upper layer can record provider failure
- **WHEN** an upper-layer market data fetch workflow catches an AkShare provider-level error
- **THEN** it can record the error message in the existing fetch log failure fields

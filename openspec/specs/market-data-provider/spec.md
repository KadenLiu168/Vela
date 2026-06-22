# market-data-provider Specification

## Purpose
Define the provider abstraction and normalized ETF daily price contract used by future market data ingestion.
## Requirements
### Requirement: Market data provider interface
The system SHALL define a `MarketDataProvider` abstraction for fetching ETF daily market prices.

#### Scenario: Fetch ETF daily prices
- **WHEN** backend code requests daily prices for an ETF symbol through a market data provider
- **THEN** the provider interface exposes a method for returning daily price rows for that symbol

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code requests daily prices with optional start and end dates
- **THEN** the provider interface accepts optional date bounds without requiring provider-specific parameters

### Requirement: Provider daily price contract
The system SHALL define a normalized daily price value object for provider results.

#### Scenario: Daily price exposes OHLCV fields
- **WHEN** backend code inspects a provider daily price value
- **THEN** it includes the ETF symbol, trade date, open price, high price, low price, close price, optional adjusted close, and optional volume

#### Scenario: Daily price is independent from persistence models
- **WHEN** provider code returns daily price values
- **THEN** those values do not require a SQLAlchemy session, `MarketPrice` ORM instance, or internal `etf_id`

### Requirement: Provider implementation independence
The system SHALL keep the market data provider contract independent from concrete data source libraries.

#### Scenario: Contract does not expose AkShare types
- **WHEN** backend code depends on the provider abstraction
- **THEN** it does not need to import AkShare or reference AkShare-specific return types

#### Scenario: Contract does not expose pandas table shape
- **WHEN** backend code depends on the provider abstraction
- **THEN** it does not need to inspect pandas `DataFrame` columns or provider-specific column names

### Requirement: Fake provider support
The system SHALL allow tests to use fake market data providers that satisfy the same contract as production providers.

#### Scenario: Fake provider returns deterministic daily prices
- **WHEN** a test supplies a fake provider implementing the market data provider interface
- **THEN** backend code can fetch deterministic ETF daily prices without network access or external data source dependencies

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

### Requirement: AkShare fetched daily price validation
The system SHALL validate AkShare ETF daily rows before returning internal `DailyPrice` values.

#### Scenario: Reject missing required row values
- **WHEN** AkShare returns an ETF daily row with a missing, null, or empty required date, OHLC price, or volume value
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid trade date
- **WHEN** AkShare returns an ETF daily row with a trade date that cannot be parsed as a calendar date
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid OHLC price
- **WHEN** AkShare returns an ETF daily row with an OHLC price that is non-numeric, non-finite, or less than or equal to zero
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject inconsistent OHLC relationship
- **WHEN** AkShare returns an ETF daily row whose high price is lower than open, low, or close, or whose low price is higher than open, high, or close
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid volume
- **WHEN** AkShare returns an ETF daily row with a volume that is non-numeric, non-integral, or negative
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Include source row context in validation failure
- **WHEN** AkShare row validation fails
- **THEN** the provider-level error includes source, symbol, requested date range, row index, failing column or field, invalid value, and validation reason where applicable

#### Scenario: Reject whole result when one row is invalid
- **WHEN** AkShare returns multiple ETF daily rows and any one row fails validation
- **THEN** the provider raises a provider-level error and returns no partial `DailyPrice` results

### Requirement: AkShare transient source retry
The system SHALL retry transient AkShare source-call failures with a simple finite retry policy before surfacing a provider-level failure.

#### Scenario: Retry temporary AkShare source failure
- **WHEN** the AkShare source call fails temporarily before returning ETF daily rows
- **THEN** the provider retries the source call using a finite retry count and simple wait policy

#### Scenario: Return rows after retry succeeds
- **WHEN** an AkShare source call fails initially but succeeds before retry attempts are exhausted
- **THEN** the provider returns normalized `DailyPrice` values for the successful source response

#### Scenario: Raise provider error after retries are exhausted
- **WHEN** all AkShare source-call retry attempts fail for a requested symbol and date range
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: Do not retry invalid returned rows
- **WHEN** AkShare returns rows that fail normalization or validation
- **THEN** the provider raises a provider-level error without retrying row normalization or validation

#### Scenario: Preserve fetch log recording for final failure
- **WHEN** an upper-layer market data fetch workflow receives a provider-level error after retry exhaustion
- **THEN** the workflow can record the final failed or partial result in the existing fetch log failure fields


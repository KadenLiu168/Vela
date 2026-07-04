## MODIFIED Requirements

### Requirement: AkShare ETF daily price provider
The system SHALL keep an AkShare-backed market data provider available as a fallback implementation for fetching ETF daily market prices, but it SHALL NOT be the default provider used by application entrypoints.

#### Scenario: Fetch ETF daily prices through AkShare
- **WHEN** backend code requests ETF daily prices from the AkShare market data provider
- **THEN** the provider fetches daily ETF行情 through AkShare `fund_etf_hist_em`

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code supplies optional start and end dates to the AkShare market data provider
- **THEN** the provider sends those bounds to AkShare using `YYYYMMDD` date strings

#### Scenario: Use unadjusted daily prices by default
- **WHEN** the AkShare market data provider requests ETF daily prices
- **THEN** it requests unadjusted AkShare data and leaves `adjusted_close` unset in returned daily price values

## ADDED Requirements

### Requirement: Default market data provider is Tencent
The system SHALL use the Tencent-backed market data provider as the default provider instantiated by application entrypoints (CLI and HTTP API).

#### Scenario: CLI default provider is Tencent
- **WHEN** the CLI `fetch-market-data` subcommand runs without an explicit provider override
- **THEN** the CLI instantiates `TencentMarketDataProvider` and passes it to the market data fetch workflow

#### Scenario: HTTP API default provider is Tencent
- **WHEN** the HTTP API constructs a market data provider without an explicit provider override
- **THEN** the API instantiates `TencentMarketDataProvider` and returns it to request handlers

#### Scenario: AkShare provider remains injectable
- **WHEN** application code passes an explicit `AkShareMarketDataProvider` instance into the fetch workflow
- **THEN** the workflow uses that AkShare instance instead of the default Tencent provider, demonstrating the AkShare implementation is still usable as a fallback

### Requirement: Tencent ETF daily price provider
The system SHALL provide a Tencent-backed market data provider for fetching ETF daily market prices by delegating to AkShare `stock_zh_a_hist_tx`.

#### Scenario: Fetch ETF daily prices through Tencent
- **WHEN** backend code requests ETF daily prices from the Tencent market data provider
- **THEN** the provider calls AkShare `stock_zh_a_hist_tx` and returns the resulting daily price rows

#### Scenario: Map bare symbol to Tencent market prefix
- **WHEN** the Tencent provider is given a bare 6-digit ETF symbol
- **THEN** the provider prefixes the symbol with `sz` for symbols starting with `15` and with `sh` for all other symbols before calling AkShare

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code supplies optional start and end dates to the Tencent market data provider
- **THEN** the provider sends those bounds to AkShare using `YYYYMMDD` date strings

#### Scenario: Use unadjusted daily prices by default
- **WHEN** the Tencent market data provider requests ETF daily prices
- **THEN** it requests unadjusted AkShare data and leaves `adjusted_close` unset in returned daily price values

### Requirement: Tencent daily price normalization
The system SHALL normalize Tencent ETF daily rows into the internal provider daily price contract.

#### Scenario: Normalize Tencent ETF OHLC fields
- **WHEN** Tencent returns ETF daily rows with `date`, `open`, `close`, `high`, and `low` columns
- **THEN** the provider returns `DailyPrice` values with symbol, trade date, open price, high price, low price, close price, optional adjusted close set to `None`, and optional volume set to `None`

#### Scenario: Drop Tencent-only amount column
- **WHEN** Tencent returns an `amount` column in addition to the OHLC columns
- **THEN** the provider does not propagate `amount` to the `DailyPrice` value (it has no corresponding field)

#### Scenario: Hide Tencent table shape from callers
- **WHEN** backend code receives values from the Tencent market data provider
- **THEN** it does not need to inspect pandas DataFrames or Tencent-specific column names

#### Scenario: Empty Tencent result
- **WHEN** Tencent returns no ETF daily rows for the requested symbol and date range
- **THEN** the provider returns an empty sequence

### Requirement: Tencent provider error propagation
The system SHALL expose Tencent provider failures as catchable provider-level errors.

#### Scenario: Tencent source call fails
- **WHEN** the AkShare `stock_zh_a_hist_tx` call raises an error while fetching ETF daily prices
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: Tencent row normalization fails
- **WHEN** Tencent returns rows that cannot be normalized into the internal daily price contract
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: Upper layer can record Tencent provider failure
- **WHEN** an upper-layer market data fetch workflow catches a Tencent provider-level error
- **THEN** it can record the error message in the existing fetch log failure fields

### Requirement: Tencent fetched daily price validation
The system SHALL validate Tencent ETF daily rows before returning internal `DailyPrice` values.

#### Scenario: Reject missing required Tencent row values
- **WHEN** Tencent returns an ETF daily row with a missing, null, or empty required date or OHLC price value
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid Tencent trade date
- **WHEN** Tencent returns an ETF daily row with a trade date that cannot be parsed as a calendar date
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid Tencent OHLC price
- **WHEN** Tencent returns an ETF daily row with an OHLC price that is non-numeric, non-finite, or less than or equal to zero
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject inconsistent Tencent OHLC relationship
- **WHEN** Tencent returns an ETF daily row whose high price is lower than open, low, or close, or whose low price is higher than open, high, or close
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Include source row context in Tencent validation failure
- **WHEN** Tencent row validation fails
- **THEN** the provider-level error includes source, symbol, requested date range, row index, failing column or field, invalid value, and validation reason where applicable

#### Scenario: Reject whole result when one Tencent row is invalid
- **WHEN** Tencent returns multiple ETF daily rows and any one row fails validation
- **THEN** the provider raises a provider-level error and returns no partial `DailyPrice` results

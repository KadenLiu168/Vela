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

### Requirement: Default market data provider is Tencent
The system SHALL use the Tencent-backed market data provider as the default provider instantiated by application entrypoints (CLI and HTTP API).

#### Scenario: CLI default provider is Tencent
- **WHEN** the CLI `fetch-market-data` subcommand runs without an explicit provider override
- **THEN** the CLI instantiates `TencentMarketDataProvider` and passes it to the market data fetch workflow

#### Scenario: HTTP API default provider is Tencent
- **WHEN** the HTTP API constructs a market data provider without an explicit provider override
- **THEN** the API instantiates `TencentMarketDataProvider` and returns it to request handlers

#### Scenario: JoinQuant provider remains injectable
- **WHEN** application code passes an explicit `JoinQuantMarketDataProvider` instance into the fetch workflow
- **THEN** the workflow uses that JoinQuant instance instead of the default Tencent provider, demonstrating JoinQuant is usable as an independent backup provider

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

#### Scenario: Use backward-adjusted daily prices by default
- **WHEN** the Tencent market data provider requests ETF daily prices
- **THEN** it requests backward-adjusted data (`adjust="hfq"`) and derives the backward-adjustment factor by fetching unadjusted data (`adjust=""`) and computing `factor = backward_adjusted_close / unadjusted_close` per row

#### Scenario: Expose backward-adjustment factor in daily price
- **WHEN** the Tencent market data provider returns ETF daily prices
- **THEN** each `DailyPrice` value carries a non-null `factor` reflecting the backward-adjustment factor for that trade date

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

### Requirement: Provider daily price ordering
The system SHALL return daily price sequences from every market data provider sorted in ascending order by trade date, regardless of the underlying data source's native row order.

#### Scenario: Return prices ascending by trade date
- **WHEN** a market data provider returns multiple `DailyPrice` values for a requested symbol and date range
- **THEN** the returned sequence is sorted in ascending order by `trade_date`

#### Scenario: Sort regardless of source row order
- **WHEN** the underlying data source returns daily rows in descending or unspecified order
- **THEN** the provider still returns `DailyPrice` values sorted in ascending order by `trade_date`

#### Scenario: Tencent provider returns ascending order
- **WHEN** the Tencent market data provider returns multiple `DailyPrice` values
- **THEN** the returned sequence is sorted in ascending order by `trade_date`, replacing the previous reliance on the source's native row order

### Requirement: Provider error type location
The system SHALL define the catchable provider-level error type (`MarketDataProviderError`) in the market data provider contract module, shared by all concrete provider implementations, rather than within any single concrete provider module.

#### Scenario: Error type imported from contract module
- **WHEN** backend code or a concrete provider implementation needs to raise or catch a provider-level error
- **THEN** it imports `MarketDataProviderError` from the contract module that also defines `DailyPrice` and the `MarketDataProvider` Protocol

#### Scenario: Concrete providers do not own the error type
- **WHEN** a concrete provider implementation (Tencent or JoinQuant) raises a provider-level error
- **THEN** the error type is the shared contract-level type, not a type defined in that concrete provider's module

### Requirement: JoinQuant ETF daily price provider
The system SHALL provide a JoinQuant-backed market data provider for fetching ETF daily market prices by delegating to the `jqdatasdk` library, independent of the `akshare` package used by the Tencent provider.

#### Scenario: Fetch ETF daily prices through JoinQuant
- **WHEN** backend code requests ETF daily prices from the JoinQuant market data provider
- **THEN** the provider authenticates with `jqdatasdk` using credentials from the environment and fetches daily ETF行情 through `jqdatasdk`

#### Scenario: Map bare symbol to JoinQuant exchange suffix
- **WHEN** the JoinQuant provider is given a bare 6-digit ETF symbol
- **THEN** the provider appends `XSHE` for symbols starting with `15` and `XSHG` for all other symbols before calling `jqdatasdk`

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code supplies optional start and end dates to the JoinQuant market data provider
- **THEN** the provider sends those bounds to `jqdatasdk` using date strings

#### Scenario: Expose backward-adjustment factor by default
- **WHEN** the JoinQuant market data provider requests ETF daily prices
- **THEN** it requests unadjusted data (`fq=None`) together with the `factor` field, and reads the `factor` field directly from `jqdatasdk` as the backward-adjustment factor per row

#### Scenario: Expose backward-adjustment factor in daily price
- **WHEN** the JoinQuant market data provider returns ETF daily prices
- **THEN** each `DailyPrice` value carries a non-null `factor` reflecting the backward-adjustment factor for that trade date

### Requirement: JoinQuant trade date index handling
The system SHALL convert the JoinQuant DataFrame trade date index into a named column before normalization, so the shared base normalization logic can read it.

#### Scenario: Promote date index to trade_date column
- **WHEN** `jqdatasdk` returns ETF daily rows with the trade date in the DataFrame index rather than a column
- **THEN** the provider sets the index name to `trade_date` and resets the index to a column before handing rows to the shared base normalization logic

### Requirement: JoinQuant credentials via environment
The system SHALL load JoinQuant credentials from environment variables and SHALL NOT read them from git-tracked configuration files or hardcode them in source.

#### Scenario: Read credentials from environment
- **WHEN** the JoinQuant market data provider is constructed
- **THEN** it reads `JQ_USERNAME` and `JQ_PASSWORD` from the environment (loading `.env` if present) and uses them to authenticate with `jqdatasdk`

#### Scenario: Reject missing credentials
- **WHEN** the JoinQuant market data provider is constructed without `JQ_USERNAME` or `JQ_PASSWORD` in the environment
- **THEN** the provider raises a provider-level error instead of attempting to fetch data

#### Scenario: Authenticate lazily and exactly once per process
- **WHEN** multiple JoinQuant market data provider instances are constructed in the same process
- **THEN** `jqdatasdk` authentication runs at most once for the process, regardless of how many instances are created

#### Scenario: Never persist credentials in git-tracked files
- **WHEN** credentials are supplied for the JoinQuant market data provider
- **THEN** they live only in `.env` (gitignored) and never appear in `config/*.yaml`, `AppConfig`, committed source, or `.env.example`

### Requirement: JoinQuant daily price normalization
The system SHALL normalize JoinQuant ETF daily rows into the internal provider daily price contract.

#### Scenario: Normalize JoinQuant ETF OHLCV fields
- **WHEN** JoinQuant returns ETF daily rows with trade date, open, high, low, close, and volume fields
- **THEN** the provider returns `DailyPrice` values with symbol, trade date, open price, high price, low price, close price, optional adjusted close set to `None`, and optional volume

#### Scenario: Hide JoinQuant table shape from callers
- **WHEN** backend code receives values from the JoinQuant market data provider
- **THEN** it does not need to inspect pandas DataFrames or JoinQuant-specific column or index names

#### Scenario: Empty JoinQuant result
- **WHEN** JoinQuant returns no ETF daily rows for the requested symbol and date range
- **THEN** the provider returns an empty sequence

### Requirement: JoinQuant provider error propagation
The system SHALL expose JoinQuant provider failures as catchable provider-level errors.

#### Scenario: JoinQuant source call fails
- **WHEN** the `jqdatasdk` call raises an error while fetching ETF daily prices
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: JoinQuant row normalization fails
- **WHEN** JoinQuant returns rows that cannot be normalized into the internal daily price contract
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: Upper layer can record JoinQuant provider failure
- **WHEN** an upper-layer market data fetch workflow catches a JoinQuant provider-level error
- **THEN** it can record the error message in the existing fetch log failure fields

### Requirement: JoinQuant optional dependency isolation
The system SHALL keep `jqdatasdk` an optional dependency so that contributors who do not install the JoinQuant extra are unaffected.

#### Scenario: Core import succeeds without JoinQuant extra
- **WHEN** the `joinquant` optional dependency is not installed
- **THEN** importing `vela_core` still succeeds and no `jqdatasdk` import is triggered at module import time

#### Scenario: JoinQuant provider usable only with extra installed
- **WHEN** backend code constructs a `JoinQuantMarketDataProvider` without the `joinquant` extra installed and without an injected source
- **THEN** the provider raises a clear error indicating the optional dependency is missing

### Requirement: Provider daily price factor field
The system SHALL include a non-null backward-adjustment factor in every provider daily price value, so that adjusted prices can be reconstructed from stored unadjusted prices.

#### Scenario: Daily price exposes factor field
- **WHEN** backend code inspects a provider daily price value
- **THEN** it includes a non-null `factor` field representing the backward-adjustment factor for that trade date

#### Scenario: Factor is independent from adjusted close column
- **WHEN** provider code returns daily price values
- **THEN** the values carry the adjustment factor directly rather than a pre-multiplied adjusted close, so callers can derive both forward- and backward-adjusted prices from the same stored unadjusted close and factor


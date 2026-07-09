## ADDED Requirements

### Requirement: JoinQuant ETF daily price provider
The system SHALL provide a JoinQuant-backed market data provider for fetching ETF daily market prices by delegating to the `jqdatasdk` library, independent of the `akshare` package used by the AkShare and Tencent providers.

#### Scenario: Fetch ETF daily prices through JoinQuant
- **WHEN** backend code requests ETF daily prices from the JoinQuant market data provider
- **THEN** the provider authenticates with `jqdatasdk` using credentials from the environment and fetches daily ETF行情 through `jqdatasdk`

#### Scenario: Map bare symbol to JoinQuant exchange suffix
- **WHEN** the JoinQuant provider is given a bare 6-digit ETF symbol
- **THEN** the provider appends `XSHE` for symbols starting with `15` and `XSHG` for all other symbols before calling `jqdatasdk`

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code supplies optional start and end dates to the JoinQuant market data provider
- **THEN** the provider sends those bounds to `jqdatasdk` using date strings

#### Scenario: Use unadjusted daily prices by default
- **WHEN** the JoinQuant market data provider requests ETF daily prices
- **THEN** it requests unadjusted data and leaves `adjusted_close` unset in returned daily price values

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

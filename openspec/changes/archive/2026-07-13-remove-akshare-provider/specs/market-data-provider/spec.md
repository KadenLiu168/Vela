## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: AkShare ETF daily price provider
**Reason**: The AkShare provider shares the same `akshare` library and `requests`/TLS stack as the default Tencent provider, so it offers no independent redundancy against the proxy/TLS failures that motivated the Tencent switch. It has no production instantiation and no automatic failover path. The independent backup role is filled by the JoinQuant provider (separate `jqdatasdk` dependency and TLS stack).
**Migration**: Use `TencentMarketDataProvider` as the default provider and `JoinQuantMarketDataProvider` as the independent backup. The `akshare` package remains a runtime dependency because the Tencent provider calls `stock_zh_a_hist_tx` through it.

### Requirement: AkShare daily price normalization
**Reason**: Removed together with the AkShare provider implementation. Normalization for the retained providers is defined by the Tencent and JoinQuant normalization requirements plus the shared base normalization logic.
**Migration**: Rely on the Tencent and JoinQuant normalization requirements; the shared `BaseMarketDataProvider` normalization skeleton is unchanged.

### Requirement: AkShare provider error propagation
**Reason**: Removed together with the AkShare provider implementation. Provider-level error propagation for the retained providers is covered by the Tencent and JoinQuant error-propagation requirements and the contract-level `MarketDataProviderError`.
**Migration**: Rely on the Tencent and JoinQuant error-propagation requirements and the contract-level error type.

### Requirement: AkShare fetched daily price validation
**Reason**: Removed together with the AkShare provider implementation. Row validation is enforced uniformly by the shared base validation logic and is exercised via the Tencent and JoinQuant validation requirements.
**Migration**: Rely on the Tencent and JoinQuant validation requirements; the shared base validation behavior is unchanged.

### Requirement: AkShare transient source retry
**Reason**: Removed together with the AkShare provider implementation. Retained providers keep their own finite retry policy via their `@retry`-decorated `_fetch_rows` hook.
**Migration**: Rely on the per-provider retry behavior of the Tencent and JoinQuant providers (3 attempts / 1s wait).

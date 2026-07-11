## MODIFIED Requirements

### Requirement: AkShare ETF daily price provider
The system SHALL keep an AkShare-backed market data provider available as a fallback implementation for fetching ETF daily market prices, but it SHALL NOT be the default provider used by application entrypoints.

#### Scenario: Fetch ETF daily prices through AkShare
- **WHEN** backend code requests ETF daily prices from the AkShare market data provider
- **THEN** the provider fetches daily ETF行情 through AkShare `fund_etf_hist_em`

#### Scenario: Fetch ETF daily prices with date bounds
- **WHEN** backend code supplies optional start and end dates to the AkShare market data provider
- **THEN** the provider sends those bounds to AkShare using `YYYYMMDD` date strings

#### Scenario: Use backward-adjusted daily prices by default
- **WHEN** the AkShare market data provider requests ETF daily prices
- **THEN** it requests backward-adjusted AkShare data (`adjust="hfq"`) and derives the backward-adjustment factor by fetching unadjusted data (`adjust=""`) and computing `factor = backward_adjusted_close / unadjusted_close` per row

#### Scenario: Expose backward-adjustment factor in daily price
- **WHEN** the AkShare market data provider returns ETF daily prices
- **THEN** each `DailyPrice` value carries a non-null `factor` reflecting the backward-adjustment factor for that trade date

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

#### Scenario: Expose backward-adjustment factor by default
- **WHEN** the JoinQuant market data provider requests ETF daily prices
- **THEN** it requests unadjusted data (`fq=None`) together with the `factor` field, and reads the `factor` field directly from `jqdatasdk` as the backward-adjustment factor per row

#### Scenario: Expose backward-adjustment factor in daily price
- **WHEN** the JoinQuant market data provider returns ETF daily prices
- **THEN** each `DailyPrice` value carries a non-null `factor` reflecting the backward-adjustment factor for that trade date

## ADDED Requirements

### Requirement: Provider daily price factor field
The system SHALL include a non-null backward-adjustment factor in every provider daily price value, so that adjusted prices can be reconstructed from stored unadjusted prices.

#### Scenario: Daily price exposes factor field
- **WHEN** backend code inspects a provider daily price value
- **THEN** it includes a non-null `factor` field representing the backward-adjustment factor for that trade date

#### Scenario: Factor is independent from adjusted close column
- **WHEN** provider code returns daily price values
- **THEN** the values carry the adjustment factor directly rather than a pre-multiplied adjusted close, so callers can derive both forward- and backward-adjusted prices from the same stored unadjusted close and factor

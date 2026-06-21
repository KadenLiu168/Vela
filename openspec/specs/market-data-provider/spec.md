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

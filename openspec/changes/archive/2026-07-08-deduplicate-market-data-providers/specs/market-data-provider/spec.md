## ADDED Requirements

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
- **WHEN** a concrete provider implementation (AkShare or Tencent) raises a provider-level error
- **THEN** the error type is the shared contract-level type, not a type defined in that concrete provider's module

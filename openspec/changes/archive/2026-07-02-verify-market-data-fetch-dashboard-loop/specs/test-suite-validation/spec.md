## ADDED Requirements

### Requirement: Market data fetch dashboard loop validation
The repository SHALL include automated pytest coverage for the COP-124 market data fetch to Dashboard closed loop.

#### Scenario: Pytest validates market data fetch dashboard loop
- **WHEN** a developer runs the API market data fetch tests through pytest
- **THEN** pytest MUST execute a test that triggers the market data fetch API with a controlled provider
- **AND** the test MUST verify persisted `MarketPrice` and `DataFetchLog` rows
- **AND** the test MUST verify a follow-up Dashboard API response reflects the newly persisted market data status and fetch operation summary

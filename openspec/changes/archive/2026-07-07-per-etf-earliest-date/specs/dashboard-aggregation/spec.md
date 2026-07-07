## MODIFIED Requirements

### Requirement: Dashboard market data status uses persisted market prices

The dashboard aggregation service SHALL calculate market data status from real `MarketPrice` rows stored in SQLite.

#### Scenario: Market price coverage summary

- **WHEN** persisted market price rows exist for multiple ETFs and trade dates
- **THEN** the market data status reports the total market price row count
- **AND** it reports the distinct covered ETF count
- **AND** it reports the earliest and latest persisted trade dates across all ETFs
- **AND** each ETF in the `etf_list` includes its own earliest persisted trade date

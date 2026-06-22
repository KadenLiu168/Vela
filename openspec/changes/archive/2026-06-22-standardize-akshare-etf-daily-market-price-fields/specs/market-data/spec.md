## ADDED Requirements

### Requirement: Provider daily price to market price mapping
The system SHALL provide a tested mapping from normalized provider daily price values into internal `MarketPrice` fields.

#### Scenario: Map provider daily price fields
- **WHEN** backend code maps a provider daily price value with an internal ETF id
- **THEN** the resulting `MarketPrice` row uses that ETF id and preserves trade date, open price, high price, low price, close price, adjusted close, and volume values

#### Scenario: Preserve explicit field types
- **WHEN** backend code maps a provider daily price value into a `MarketPrice` row
- **THEN** trade date remains a date value, price fields remain decimal values, and volume remains an optional integer value

#### Scenario: Keep provider mapping independent from ETF lookup
- **WHEN** backend code maps a provider daily price value into a `MarketPrice` row
- **THEN** the mapper does not query ETF metadata or infer `etf_id` from the provider symbol

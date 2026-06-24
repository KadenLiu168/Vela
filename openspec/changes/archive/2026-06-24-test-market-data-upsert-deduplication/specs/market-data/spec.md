## MODIFIED Requirements

### Requirement: Market price upsert persistence
The system SHALL provide SQLite upsert behavior for daily ETF market prices using ETF and trading date as the row identity.

#### Scenario: Insert new market price
- **WHEN** backend code upserts a market price whose `etf_id` and `trade_date` are not present in SQLite
- **THEN** the system inserts a new `market_price` row

#### Scenario: Prevent duplicate ETF trading date rows
- **WHEN** backend code upserts a market price with the same `etf_id` and `trade_date` as an existing row
- **THEN** the system keeps one row for that ETF and trading date

#### Scenario: Update existing market price
- **WHEN** backend code upserts a market price with the same `etf_id` and `trade_date` as an existing row but different price or volume fields
- **THEN** the system updates the existing row with the supplied market price fields

#### Scenario: Preserve different ETFs on same trading date
- **WHEN** backend code upserts market prices for different ETFs on the same trading date
- **THEN** the system stores one row per ETF

#### Scenario: Report upsert counts
- **WHEN** backend code upserts market prices
- **THEN** the system returns separate counts for inserted rows and updated rows

#### Scenario: Handle duplicate keys in one batch
- **WHEN** backend code upserts multiple market prices with the same `etf_id` and `trade_date` in one call
- **THEN** the system stores one row for that key using the last supplied market price values

#### Scenario: Verify duplicate batch persistence
- **WHEN** backend code upserts duplicate market prices for one ETF and one trading date in one call
- **THEN** the persisted `market_price` table contains exactly one row for that ETF and trading date

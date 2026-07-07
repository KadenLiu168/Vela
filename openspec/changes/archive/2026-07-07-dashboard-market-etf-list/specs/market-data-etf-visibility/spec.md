## ADDED Requirements

### Requirement: Dashboard API returns ETF list with market data

The system SHALL include an `etf_list` field in the dashboard `/api/dashboard` response under `market_data`, listing ETFs that have at least one row in `MarketPrice`.

Each entry SHALL contain `exchange`, `symbol`, and `name` fields sourced from the `etf_info` table.
The list SHALL be ordered by exchange then symbol, alphabetically.
When no `MarketPrice` rows exist, `etf_list` SHALL be an empty array.

#### Scenario: ETFs with market data are returned
- **WHEN** a GET request is made to `/api/dashboard`
- **THEN** the response MUST contain `market_data.etf_list` as an array of objects
- **AND** each object MUST have `exchange` (string), `symbol` (string), and `name` (string)
- **AND** only ETFs present in the `MarketPrice` table SHALL be included

#### Scenario: No market data exists
- **WHEN** the `MarketPrice` table is empty
- **THEN** `etf_list` SHALL be `[]`
- **AND** `covered_etfs` SHALL be 0

### Requirement: Dashboard UI displays ETF badges

The Market Data card on the dashboard SHALL render each entry in `etf_list` as a badge showing `symbol` and `name`.

Badges SHALL appear between the metric row (Price rows / Covered ETFs) and the compact date list (Earliest / Latest trade date). Badges SHALL flow in a flex-wrap row, each containing the symbol on the first line and the name on the second line. Badge styling SHALL use design system tokens from `tokens.css`.

#### Scenario: Market data card shows ETF badges
- **WHEN** the dashboard page renders with non-empty `market_data.etf_list`
- **THEN** each ETF badge MUST display its `symbol` and `name`
- **AND** badges MUST be visually contained within the Market Data card

#### Scenario: Empty ETF list renders nothing
- **WHEN** `market_data.etf_list` is `[]`
- **THEN** no ETF badge section SHALL be rendered
- **AND** the card layout SHALL remain intact

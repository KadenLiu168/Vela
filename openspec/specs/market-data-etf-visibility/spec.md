# market-data-etf-visibility Specification

## Purpose
TBD - created by archiving change dashboard-market-etf-list. Update Purpose after archive.
## Requirements
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

### Requirement: Dashboard UI displays ETF rows

The Market Data card on the dashboard SHALL render each entry in `etf_list` as a flat list of `.etf-row` elements inside a 2-column grid container (`.etf-row-list`).

Each row SHALL show a colored accent bar, the symbol in monospace, a dot separator, and the full name. The grid SHALL use `grid-template-columns: repeat(2, minmax(0, 1fr))` for strict 50/50 column distribution. Per-row border-top separators SHALL NOT be used.

#### Scenario: Market data card shows ETF rows in 2-column grid
- **WHEN** the dashboard page renders with non-empty `market_data.etf_list`
- **THEN** each ETF SHALL render as an `.etf-row` directly inside `.etf-row-list` with no category grouping
- **AND** each ETF row MUST display its `symbol` and `name`
- **AND** rows MUST be arranged in a 2-column grid

#### Scenario: Empty ETF list renders nothing
- **WHEN** `market_data.etf_list` is `[]`
- **THEN** no `.etf-row-list` container SHALL be rendered
- **AND** the card layout SHALL remain intact


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

### Requirement: Dashboard UI displays ETF groups

The Market Data card on the dashboard SHALL render each entry in `etf_list` within category-grouped sub-panels, each showing `symbol` and `name` per row.

Groups SHALL appear between the coverage timeline and the card bottom. Each group SHALL be a bordered sub-panel (`.etf-group`) with:
- A colored accent bar (3px wide, 12px tall) matching the ETF's category color
- An uppercase category heading (e.g. "US Equities", "HK Equities", "China Equities", "Bonds")
- ETF rows arranged in a 2-column CSS grid, each row showing symbol in monospace followed by a dot separator and the full name

ETF rows SHALL NOT have per-row border-top separators; the group border provides the visual enclosure.

#### Scenario: Market data card shows ETF groups
- **WHEN** the dashboard page renders with non-empty `market_data.etf_list`
- **THEN** each ETF SHALL be placed into a category-based `.etf-group` sub-panel
- **AND** each ETF row MUST display its `symbol` and `name` within the group
- **AND** groups MUST be visually contained within the Market Data card

#### Scenario: Empty ETF list renders nothing
- **WHEN** `market_data.etf_list` is `[]`
- **THEN** no `.etf-groups` container SHALL be rendered
- **AND** the card layout SHALL remain intact

#### Scenario: Category color mapping matches barColor helper
- **WHEN** an ETF belongs to a recognized category
- **THEN** the group heading accent bar SHALL use the same color as the ETF's `.etf-row-bar`
- **AND** the mapping SHALL be: `equity_us` → `var(--color-iris-violet)`, `equity_hk` → `var(--color-signal-teal)`, `equity_cn` and `bond` → `var(--color-coral-red)`
- **AND** unknown categories SHALL fall back to `var(--color-fog)`


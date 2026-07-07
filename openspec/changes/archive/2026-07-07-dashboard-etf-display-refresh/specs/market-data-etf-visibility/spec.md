## MODIFIED Requirements

### Requirement: Dashboard API returns ETF list with market data

The system SHALL include an `etf_list` field in the dashboard `/api/dashboard` response under `market_data`, listing ETFs that have at least one row in `MarketPrice`.

Each entry SHALL contain `exchange`, `symbol`, `name`, and `category` fields sourced from the `etf_info` table.
The list SHALL be ordered by exchange then symbol, alphabetically.
When no `MarketPrice` rows exist, `etf_list` SHALL be an empty array.

#### Scenario: ETFs with market data are returned
- **WHEN** a GET request is made to `/api/dashboard`
- **THEN** the response MUST contain `market_data.etf_list` as an array of objects
- **AND** each object MUST have `exchange` (string), `symbol` (string), `name` (string), and `category` (string)
- **AND** only ETFs present in the `MarketPrice` table SHALL be included

#### Scenario: No market data exists
- **WHEN** the `MarketPrice` table is empty
- **THEN** `etf_list` SHALL be `[]`
- **AND** `covered_etfs` SHALL be 0

### Requirement: Dashboard UI displays ETF badges

The Market Data card on the dashboard SHALL render each entry in `etf_list` as a row showing a market region color bar, `symbol`, and `name`.

Each row SHALL:
- Include a 3px color bar at the left edge indicating the ETF's market region, determined by `category`
- Color mapping: `equity_cn_*` / `bond_*` → `--color-coral-red` (A 股), `equity_us*` → `--color-iris-violet` (美股), `equity_hk_*` → `--color-signal-teal` (港股), other → `--color-fog`
- Display the symbol in `--font-berkeley-mono` (monospace) followed by `·` and the name in the same line
- Use `--color-paper` for symbol text and `--color-fog` for the name
- Span the full card width with padding on both sides

Rows SHALL appear between the metric row (Price rows / Covered ETFs) and the compact date list (Earliest / Latest trade date). Rows SHALL be separated by a 1px `--color-graphite` top border (first row without top border) and SHALL highlight to `--surface-slate` on hover. Row styling SHALL use design system tokens from `tokens.css`.

#### Scenario: Market data card shows ETF rows with region color bars
- **WHEN** the dashboard page renders with non-empty `market_data.etf_list`
- **THEN** each ETF row MUST display its region color bar, `symbol` and `name`
- **AND** rows MUST be visually contained within the Market Data card

#### Scenario: Empty ETF list renders nothing
- **WHEN** `market_data.etf_list` is `[]`
- **THEN** no ETF row section SHALL be rendered
- **AND** the card layout SHALL remain intact

#### Scenario: ETF row highlights on hover
- **WHEN** the user hovers over an ETF row
- **THEN** the row background SHALL change to `--surface-slate`

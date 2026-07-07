## MODIFIED Requirements

### Requirement: Market data card internal layout

The Market data card (`.market-panel`) SHALL render its content in the following order from top to bottom:

1. **Metric row** — two `.metric` tiles in a 2-column grid: "Price rows" (total row count) and "Covered ETFs" (number of ETFs with data).
2. **Coverage timeline** — a horizontal layout with earliest trade date on the left, a graphite connector bar in the middle, and latest trade date on the right. Each date endpoint shows a label (uppercase "Earliest" / "Latest") above the date in monospace.
3. **ETF list** — ETFs rendered as a flat single-column list with no category grouping.

#### Scenario: Coverage timeline shows date range

- **WHEN** the Dashboard renders the Market panel with non-null `earliest_trade_date` and `latest_trade_date`
- **THEN** a `.coverage-timeline` element SHALL appear between the metric row and the ETF list
- **AND** it SHALL display `Earliest` label above the earliest date on the left and `Latest` label above the latest date on the right
- **AND** a `.coverage-timeline-bar` SHALL connect the two endpoints

#### Scenario: Coverage timeline omitted when dates are null

- **WHEN** `earliest_trade_date` or `latest_trade_date` is null
- **THEN** NO `.coverage-timeline` SHALL be rendered

#### Scenario: ETF list renders as flat single-column grid

- **WHEN** the Dashboard renders the Market panel with a non-empty `etf_list`
- **THEN** each ETF SHALL render as an `.etf-row` directly inside `.etf-row-list` with no category grouping
- **AND** `.etf-row-list` SHALL use a single-column CSS grid (`grid-template-columns: 1fr`)
- **AND** each ETF row SHALL show a colored accent bar, the symbol in monospace, `·`, the full name, and the `earliest_trade_date` at the right end
- **AND** rows SHALL NOT have border-top separators; hover SHALL show `background: var(--surface-slate)`

#### Scenario: Empty ETF list renders nothing

- **WHEN** `etf_list` is empty
- **THEN** no `.etf-row-list` container SHALL be rendered
- **AND** the card content SHALL stop after the coverage timeline (or metric row if timeline is also absent)

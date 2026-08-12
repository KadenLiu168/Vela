# backtest-results-ui Specification

## Purpose
Defines the redesigned presentation layer for backtest results: the Detail Overview hero, the side-by-side strategy↔benchmark comparison matrix, progressive disclosure of secondary metric groups, the equity-curve legend / direct-labels / stable-colors / axes, and the Backtest List metric columns.

## ADDED Requirements

### Requirement: Backtest detail shows a side-by-side strategy versus benchmark comparison matrix
The Backtest Detail Overview SHALL present one semantic comparison table with columns Metric, Strategy, Equal-weight monthly rebalanced portfolio, and CSI 300 buy-and-hold when both fixed benchmarks are available. Its Absolute metrics row group SHALL show Total return, CAGR (calendar-time), Max drawdown, Annualized volatility (252D), Sharpe (daily returns, 252D), Sortino (rf MAR, 252D), Calmar (calendar CAGR / |MaxDD|), and longest-drawdown duration/date/recovery evidence owned by each entity. Its Strategy-relative row group SHALL show Tracking Error (252D), Information Ratio (252D), Monthly Up/Down Capture (selected months) with selected-month counts, and strategy total/annualized-return differences in the corresponding benchmark column while the Strategy cell is `n/a`. Null API values SHALL render through existing unavailable formatting and SHALL NOT be calculated in the browser.

#### Scenario: Matrix layout aligns strategy and benchmarks
- **WHEN** a benchmark-enabled backtest detail loads
- **THEN** the page renders one matrix with a column for the strategy and one column per benchmark
- **AND** each metric definition occupies exactly one row shared across all columns

#### Scenario: Relative rows are present (方案 A)
- **WHEN** the comparison matrix renders a benchmark column
- **THEN** the table includes both the absolute and Strategy-relative row groups
- **AND** each relative value appears under the benchmark it compares against while the Strategy cell is `n/a`
- **AND** Up/Down capture retains its selected-month observation count

#### Scenario: Comparable absolute rows use a documented highlight rule
- **WHEN** an absolute numeric row has at least two non-null comparable values
- **THEN** Total return, CAGR, Sharpe, Sortino, and Calmar select the numerically greatest value
- **AND** Max drawdown selects the value closest to zero, while Volatility and longest drawdown duration select the numerically smallest value
- **AND** every tied best cell is marked with visible or assistive `Best` text so the distinction does not rely on color alone

#### Scenario: Non-comparable evidence is not ranked
- **WHEN** the table renders dates, recovery status, a relative row, a null value, or a row with fewer than two non-null comparable values
- **THEN** no best-value marker is applied to that evidence

#### Scenario: Legacy detail without benchmarks remains truthful
- **WHEN** a legacy backtest detail returns an empty benchmark collection
- **THEN** the strategy hero and other strategy-owned evidence remain available
- **AND** the page shows an explicit no-benchmark comparison state instead of fabricating benchmark columns or relative values

### Requirement: Backtest detail shows strategy headline metrics as a hero
The Backtest Detail Overview SHALL show a hero region containing exactly the strategy's Total return, CAGR (calendar-time), Sharpe (daily returns, 252D), and Max drawdown as four prominent cards before the comparison table in DOM and visual order, replacing the prior full strategy MetricCard grid.

#### Scenario: Hero cards show strategy-only headline metrics
- **WHEN** the detail page loads
- **THEN** it shows four cards for strategy Total return, CAGR (calendar-time), Sharpe (daily returns, 252D), and Max drawdown before the comparison table
- **AND** benchmark metrics are not duplicated in the hero
- **AND** nullable values use the existing unavailable formatting

### Requirement: Secondary metric groups use progressive disclosure
The Backtest Detail page SHALL render distribution-risk evidence, return stability, and CSI-300 CAPM evidence inside three native `<details>` disclosures that are closed by default. Collapsing SHALL change presentation only: owner identity, evidence statuses, observation counts, exact-value tables, and existing null explanations SHALL remain intact when expanded.

#### Scenario: Secondary groups are collapsible
- **WHEN** the detail page renders the distribution, rolling-stability, and CAPM sections
- **THEN** each is inside a closed-by-default disclosure with an accessible `<summary>` label
- **AND** every disclosure is operable by keyboard and reveals its complete existing evidence when expanded

### Requirement: Equity curve legend identifies each series by color and label
The equity-curve chart SHALL render a legend where each entry shows a color swatch whose fill matches the corresponding line stroke, and SHALL render a readable direct label of the series name at the end of each line. Colors SHALL be assigned from the explicit stable mapping for `strategy`, `equal_weight_monthly`, and `csi_300_buy_hold`, not from array position. The same mapping SHALL be used by Return Stability rolling charts.

#### Scenario: Legend swatch matches line color
- **WHEN** the equity-curve legend lists a series
- **THEN** its swatch fill equals the stroke color of that series line
- **AND** the series name is shown as text alongside the swatch

#### Scenario: Each line carries a direct end-label
- **WHEN** the equity curve renders a series line
- **THEN** the series name is drawn at the line's end point
- **AND** the label color matches the line stroke
- **AND** labels are deterministically separated when endpoints converge and remain inside the SVG viewBox

#### Scenario: Missing series does not reassign identity
- **WHEN** one fixed benchmark has no plottable points
- **THEN** every remaining current series keeps the token assigned to its key
- **AND** strategy and the other fixed benchmark do not shift to another series color

### Requirement: Equity curve renders axes
The equity-curve chart SHALL render an x-axis with date ticks and a y-axis with net-value ticks. Return Stability rolling charts SHALL use the same shared tick geometry while formatting the y-axis for the selected Return, Volatility, or Sharpe metric. All tick and endpoint geometry SHALL derive from `EQUITY_CURVE_CHART` and the same shared sorted-date/value scale as the line paths.

#### Scenario: Axes and ticks are present
- **WHEN** the equity curve renders
- **THEN** it shows date ticks along the x-axis and net-value ticks along the y-axis
- **AND** the geometry derives from the `EQUITY_CURVE_CHART` dimensions constant

#### Scenario: Rolling chart uses metric-correct axes and exact fallback
- **WHEN** the user selects a rolling Return, Volatility, or Sharpe chart
- **THEN** its x-axis shows dates and its y-axis labels use the selected metric's format without mixing metric scales
- **AND** the accessible exact-value table remains available

#### Scenario: Existing chart fallback states remain safe
- **WHEN** the strategy curve is empty, contains one valid point, or all plotted values are equal
- **THEN** the existing empty/single-point feedback or deterministic equal-range geometry remains available
- **AND** no tick, path, endpoint label, or summary value is non-finite or outside the SVG viewBox

### Requirement: Backtest list shows key metric columns
The Backtest List table SHALL include Total return, CAGR (calendar-time), and Sharpe (daily returns, 252D) columns sourced from the already-returned `BacktestListItem` fields, in addition to the existing Run / Date range / Status / Started at columns.

#### Scenario: List columns use existing item fields
- **WHEN** the backtest list renders a row
- **THEN** it shows Total return, CAGR (calendar-time), and Sharpe (daily returns, 252D) derived from `total_return`, `annualized_return`, and `sharpe_ratio` on the list item
- **AND** no new API field is required to populate those columns
- **AND** completed and legacy/null rows use the existing percent/decimal/unavailable formatters without browser-side financial derivation

### Requirement: Dense result views remain responsive and keyboard accessible
The comparison matrix and expanded Backtest List table SHALL use labeled, keyboard-scrollable local horizontal-overflow regions when needed. The comparison matrix metric-name column SHALL remain sticky within its local region. At 1440×1000 and 390×844 the pages SHALL have no page-level horizontal overflow, and chart ticks/end-labels SHALL remain readable and inside their SVG viewBoxes.

#### Scenario: Desktop and narrow browser acceptance
- **WHEN** benchmark-enabled Backtest Detail and populated Backtest List states render at 1440×1000 or 390×844
- **THEN** hero metrics, matrix/list columns, disclosures, chart axes, labels, legends, and existing navigation remain reachable and readable
- **AND** horizontal scrolling, when necessary, is confined to a labeled local region operable by keyboard

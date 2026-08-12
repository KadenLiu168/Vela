# backtest-results-ui Specification Delta

## MODIFIED Requirements

### Requirement: Backtest detail shows a side-by-side strategy versus benchmark comparison matrix
The Backtest Detail Overview SHALL present benchmark comparison in two groups: a core metrics table that is always visible, and an Advanced Metrics disclosure that is closed by default. The core metrics table SHALL render columns Metric, Strategy, Equal-weight monthly rebalanced portfolio, and CSI 300 buy-and-hold when both fixed benchmarks are available, with rows Total return, CAGR (calendar-time), Max drawdown, Annualized volatility (252D), Sharpe (daily returns, 252D), Sortino (rf MAR, 252D), and Calmar (calendar CAGR / |MaxDD|). Best-value markers SHALL follow the existing documented direction rules on comparable absolute numeric rows. The Advanced Metrics disclosure SHALL contain the remaining matrix evidence: longest-drawdown duration/peak/trough/recovery, Tracking Error (252D), Information Ratio (252D), Monthly Up/Down Capture (selected months) with selected-month counts, and strategy total/annualized-return differences in the corresponding benchmark column while the Strategy cell is `n/a`. Null API values SHALL render through existing unavailable formatting and SHALL NOT be financially derived in the browser.

#### Scenario: Core table aligns strategy and benchmarks
- **WHEN** a benchmark-enabled backtest detail loads
- **THEN** the core table renders one column for the strategy and one column per benchmark
- **AND** each core metric definition occupies exactly one row shared across all columns

#### Scenario: Advanced metrics are collapsed by default
- **WHEN** the benchmark comparison region renders
- **THEN** the Advanced Metrics group is a closed-by-default disclosure reachable by keyboard
- **AND** expanding it reveals drawdown duration/date/recovery evidence, Tracking Error, Information Ratio, Up/Down Capture with selected-month counts, and the strategy difference rows

#### Scenario: Relative rows live in the advanced group
- **WHEN** the Advanced Metrics disclosure is expanded
- **THEN** each relative value appears under the benchmark it compares against while the Strategy cell is `n/a`
- **AND** Up/Down capture retains its selected-month observation count

#### Scenario: Comparable absolute rows use a documented highlight rule
- **WHEN** a core-table absolute numeric row has at least two non-null comparable values
- **THEN** Total return, CAGR, Sharpe, Sortino, and Calmar select the numerically greatest value
- **AND** Max drawdown selects the value closest to zero, while Volatility selects the numerically smallest value
- **AND** every tied best cell is marked with visible or assistive `Best` text so the distinction does not rely on color alone

#### Scenario: Non-comparable evidence is not ranked
- **WHEN** a table renders dates, recovery status, a relative row, a null value, or a row with fewer than two non-null comparable values
- **THEN** no best-value marker is applied to that evidence

#### Scenario: Legacy detail without benchmarks remains truthful
- **WHEN** a legacy backtest detail returns an empty benchmark collection
- **THEN** the strategy-owned evidence and the Decision Summary remain available
- **AND** the page shows an explicit no-benchmark comparison state instead of fabricating benchmark columns or relative values

### Requirement: Backtest detail shows strategy headline metrics as a hero
The Backtest Detail Overview SHALL present a Decision Summary as the first content region after the run summary line, replacing the prior four-card hero. It SHALL show the strategy's Total return, CAGR (calendar-time), Sharpe (daily returns, 252D), and Max drawdown, and SHALL show each metric's difference versus the Primary Benchmark. CAGR and Total return differences SHALL use the backend-provided `annualized_return_difference` and `total_return_difference` fields. Sharpe and Max drawdown differences SHALL be plain arithmetic subtraction of the API-provided non-null benchmark value from the API-provided non-null strategy value; this is display arithmetic on already-provided numbers, never financial derivation. Max drawdown difference SHALL be framed as shallower/deeper relative to the benchmark, where a value closer to zero is favorable. Null API values SHALL render through existing unavailable formatting and SHALL NOT be financially derived in the browser. The Primary Benchmark SHALL be the benchmark whose key is `csi_300_buy_hold` when present, otherwise the first benchmark in the API collection; with no benchmarks the region SHALL show the four strategy values without difference evidence.

#### Scenario: Decision summary shows strategy values and primary benchmark differences
- **WHEN** a benchmark-enabled backtest detail loads
- **THEN** the region shows the four strategy headline values and their four differences against the Primary Benchmark
- **AND** CAGR and Total return differences come from the API difference fields while Sharpe and Max drawdown differences come from display-level subtraction of non-null API values

#### Scenario: Primary benchmark falls back to the first benchmark
- **WHEN** the benchmark collection has no `csi_300_buy_hold` entry but is non-empty
- **THEN** the first benchmark in the API collection serves as the Primary Benchmark for difference evidence

#### Scenario: No benchmarks keeps strategy values visible
- **WHEN** a backtest detail returns an empty benchmark collection
- **THEN** the Decision Summary shows the four strategy values with the existing unavailable formatting
- **AND** no benchmark column or difference evidence is fabricated

### Requirement: Secondary metric groups use progressive disclosure
The Backtest Detail Overview SHALL render distribution-risk evidence, return stability, and CSI-300 CAPM evidence inside the Deep Analysis region, each inside its own native `<details>` disclosure that is closed by default. Collapsing SHALL change presentation only: owner identity, evidence statuses, observation counts, exact-value tables, and existing null explanations SHALL remain intact when expanded.

#### Scenario: Deep analysis groups are collapsible
- **WHEN** the detail page renders the Deep Analysis region
- **THEN** the distribution, rolling-stability, and CAPM sections each sit in a closed-by-default disclosure with an accessible `<summary>` label
- **AND** every disclosure is operable by keyboard and reveals its complete existing evidence when expanded

## ADDED Requirements

### Requirement: Backtest detail presents overview sections in the research order
The Backtest Detail Overview SHALL order its content regions top-to-bottom as: run summary line, Decision Summary, Equity Curve, Benchmark Comparison, Deep Analysis, and Experiment Config. The run summary line SHALL show strategy id, date range, and status in one line. The full run metadata (config version, started/finished timestamps, error message) SHALL be presented in the Experiment Config region. The Signals tab and its lazy loading behavior SHALL remain unchanged.

#### Scenario: Sections follow the research order
- **WHEN** a benchmark-enabled backtest detail loads
- **THEN** the run summary line appears first, followed by the Decision Summary, the Equity Curve, the Benchmark Comparison, the Deep Analysis, and the Experiment Config regions in DOM and visual order

#### Scenario: Run metadata moves to experiment config
- **WHEN** the user opens the Experiment Config region
- **THEN** the full run metadata (config version, started at, finished at, error message) is available there
- **AND** the first-screen run summary shows only strategy, date range, and status

### Requirement: Experiment config presents human-readable parameters with raw fallback
The Experiment Config region SHALL render the run's `parameters_json` as a human-readable key-value list. Known keys SHALL use a documented label and value formatting: `strategy_id` (label "Strategy"), `config_version` (label "Config version"), `type` (label "Strategy type"), `start_date` and `end_date` (formatted dates), `risk_free_rate` (annualized percentage, e.g. `0.02` renders as `2.0%`), and the metric version keys (`performance_metric_version`, `equity_model_version`, `tail_distribution_metric_version`, `benchmark_regime_metric_version`) rendered as plain version text. Unknown keys SHALL fall back to their raw key and value text. The region SHALL also retain a Raw Parameters disclosure, closed by default, that renders the original JSON through the existing parameter summary formatting. No API change is required; all values come from the existing `run.parameters_json` string.

#### Scenario: Known keys render human-readable labels and formats
- **WHEN** the Experiment Config region renders a parameters payload containing known keys
- **THEN** each known key appears under its documented label with its documented formatting
- **AND** the `risk_free_rate` value is rendered as an annualized percentage rather than its raw decimal

#### Scenario: Unknown keys fall back to raw text
- **WHEN** the parameters payload contains a key outside the documented mapping
- **THEN** that key renders with its raw key name and raw value text

#### Scenario: Raw parameters remain available
- **WHEN** the Experiment Config region renders
- **THEN** a closed-by-default Raw Parameters disclosure contains the original JSON via the existing parameter summary formatting

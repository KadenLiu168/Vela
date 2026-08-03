## ADDED Requirements

### Requirement: Backtest detail shows benchmark comparison
The Backtest Detail Overview SHALL render the strategy's existing metrics together with separately labeled metric groups for "Equal-weight monthly rebalanced portfolio" and "CSI 300 buy-and-hold". Each benchmark group SHALL show its five metrics and strategy-minus-benchmark total-return and CAGR differences.

#### Scenario: Detail renders two benchmark groups
- **WHEN** a benchmark-enabled backtest detail loads
- **THEN** the Overview renders one labeled group for each fixed benchmark
- **AND** each group shows its metrics and the two relative-return differences

#### Scenario: Legacy detail has no fabricated benchmark group
- **WHEN** a legacy backtest detail has an empty benchmark collection
- **THEN** the existing strategy metrics and curve remain visible
- **AND** the page does not present fabricated benchmark values

### Requirement: Backtest detail compares three net-value curves
For a benchmark-enabled run, the Backtest Detail Overview SHALL render strategy, equal-weight monthly, and CSI 300 buy-and-hold net-value series on one accessible chart with a distinguishable legend. The chart SHALL retain its existing empty and single-strategy-curve states for legacy data.

#### Scenario: Three-series chart is distinguishable
- **WHEN** all three curve series are available
- **THEN** the chart renders all three series with a visible legend and distinguishable styling
- **AND** every series is plotted against its ordered trade dates

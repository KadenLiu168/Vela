## ADDED Requirements

### Requirement: Benchmark downside and active-risk comparison
Each fixed benchmark SHALL calculate Sortino, Calmar and longest drawdown duration from its own curve using the same definitions and risk-free-rate input as the strategy. Each benchmark result SHALL additionally retain strategy-relative Tracking Error and Information Ratio calculated from the strategy and that benchmark's exactly aligned daily returns.

#### Scenario: Dual benchmarks retain separate active metrics
- **WHEN** a benchmark-enabled backtest completes with valid dispersed active returns
- **THEN** each fixed benchmark contains its own Tracking Error and Information Ratio relative to the strategy
- **AND** contains benchmark Sortino, Calmar and longest drawdown duration

#### Scenario: Identical strategy and benchmark returns
- **WHEN** strategy and one benchmark have identical aligned daily returns
- **THEN** that comparison has Tracking Error `0.000000` and null Information Ratio

#### Scenario: Existing benchmark conventions remain unchanged
- **WHEN** expanded benchmark metrics are calculated
- **THEN** the existing benchmark total return, 365-day CAGR, maximum drawdown, 252-day volatility and Sharpe definitions and values remain unchanged

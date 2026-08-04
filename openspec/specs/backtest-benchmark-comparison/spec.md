# backtest-benchmark-comparison Specification

## Purpose
Defines the fixed benchmark calculations and comparison semantics for benchmark-enabled backtests.

## Requirements

### Requirement: Fixed benchmark definitions
The system SHALL calculate exactly two fixed reference benchmarks for each benchmark-enabled backtest: `equal_weight_monthly` named "Equal-weight monthly rebalanced portfolio" and `csi_300_buy_hold` named "CSI 300 buy-and-hold". The former SHALL use the run's dated active ETF universe with equal target weights; the latter SHALL use active `SSE:510300` as its investable CSI 300 proxy.

#### Scenario: Same-universe equal-weight benchmark
- **WHEN** a benchmark-enabled backtest starts with an active ETF universe
- **THEN** the equal-weight benchmark includes every ETF eligible on each official session
- **AND** assigns equal weights across that dated universe

#### Scenario: CSI 300 proxy identity
- **WHEN** a benchmark-enabled backtest resolves the CSI 300 benchmark
- **THEN** it uses the active ETF whose exchange and symbol are `SSE` and `510300`
- **AND** it does not require or synthesize an index `000300` price series

### Requirement: Benchmark trading and valuation semantics
Both benchmarks SHALL initialize at the first requested official session without an entry transaction cost and SHALL value holdings with the existing forward-adjusted price-ratio convention. The equal-weight benchmark SHALL rebalance only after valuation on subsequent last official sessions of a calendar month and SHALL apply the strategy configuration's `transaction_cost_bps`; the CSI 300 benchmark SHALL remain buy-and-hold after initialization.

#### Scenario: Initial allocation does not charge cost
- **WHEN** either benchmark creates its first position on the first requested official session
- **THEN** its initial net value is not reduced by transaction cost

#### Scenario: Monthly equal-weight rebalance charges cost
- **WHEN** a subsequent monthly rebalance changes the equal-weight benchmark's actual holdings
- **THEN** it charges the configured transaction cost against turnover before allocating equal target weights

#### Scenario: CSI 300 has no later rebalance
- **WHEN** the CSI 300 benchmark advances after its initial allocation
- **THEN** it changes only through the `SSE:510300` price ratio
- **AND** it incurs no later transaction cost

### Requirement: Benchmark input completeness
Benchmark-enabled backtests SHALL use the identical ordered official-session axis as the strategy and SHALL require a unique active `SSE:510300` row plus a stored price on every requested official session. The system MUST fail before signal generation or result persistence on any missing benchmark identity or price and MUST NOT shorten, forward-fill, or zero-fill the benchmark series.

#### Scenario: Missing CSI 300 price fails before artifacts
- **WHEN** `SSE:510300` lacks a price on an official session in the requested range
- **THEN** the backtest fails with the ETF identity and missing date
- **AND** it persists no signal, run, strategy curve, benchmark, or benchmark curve from that attempt

#### Scenario: Complete benchmark inputs share strategy dates
- **WHEN** all required strategy and benchmark prices are present
- **THEN** each benchmark curve has one point for every strategy curve trade date

### Requirement: Benchmark metrics and relative comparison
The system SHALL calculate total return, calendar-time annualized return, maximum drawdown, annualized volatility, and Sharpe ratio for each benchmark using the same metric definitions as the strategy. It SHALL calculate strategy minus benchmark total-return and annualized-return differences without treating them as Tracking Error, Information Ratio, Alpha, or Beta.

#### Scenario: Benchmark metric convention matches strategy
- **WHEN** strategy and benchmark curves have the same deterministic net-value inputs
- **THEN** their corresponding metrics use the same total-return, 365-day CAGR, 252-day volatility, risk-free-rate, Sharpe, and maximum-drawdown conventions

#### Scenario: Relative return values are exposed
- **WHEN** a benchmark-enabled backtest completes
- **THEN** the result contains one total-return difference and one annualized-return difference for each fixed benchmark
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

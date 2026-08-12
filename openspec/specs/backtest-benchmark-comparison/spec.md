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
Both benchmarks SHALL use the shared resolved official-session panel. They SHALL initialize at the first session on which their complete target is executable without entry cost and SHALL value holdings by resolved adjusted-value ratios. A confirmed full-day non-trading holding SHALL retain unchanged adjusted value and remain non-tradable. Equal-weight monthly targets SHALL arise only on the existing schedule, use configured transaction costs, and defer atomically when any changed leg is non-tradable; a newer scheduled target replaces an older pending target. CSI 300 SHALL remain buy-and-hold after its initial executable allocation.

#### Scenario: Initial allocation does not charge cost
- **WHEN** either benchmark's initial target contains only tradable legs
- **THEN** it initializes without transaction cost

#### Scenario: Monthly equal-weight rebalance charges cost
- **WHEN** a scheduled equal-weight target becomes wholly tradable after being immediately executable or deferred
- **THEN** it executes all changed legs once and charges configured cost against turnover once

#### Scenario: CSI 300 has no later rebalance
- **WHEN** CSI 300 advances after initial allocation
- **THEN** it changes only through resolved `SSE:510300` valuation
- **AND** incurs no later transaction cost

#### Scenario: Blocked initial allocation remains cash
- **WHEN** an initial benchmark target includes a non-tradable ETF
- **THEN** the complete target remains pending and the benchmark remains cash

#### Scenario: New monthly target replaces pending target
- **WHEN** another scheduled equal-weight target occurs before the prior target executes
- **THEN** the newer complete target replaces the pending target

#### Scenario: Confirmed non-trading benchmark session is explicit
- **WHEN** a benchmark holding has authoritative full-day non-trading status
- **THEN** that session contributes an unchanged adjusted valuation and remains present in the curve

### Requirement: Benchmark input completeness
Benchmark-enabled backtests SHALL use the strategy's identical ordered official-session axis and shared resolver. They MUST require a unique listed active `SSE:510300` identity and exactly one admissible source state for every required benchmark ETF/session. Unknown gaps, absent listing metadata, conflicts, and missing carry anchors MUST fail before artifacts; confirmed full-day status MAY resolve through the shared non-trading policy. The system MUST NOT shorten a series, infer a status, or create raw zero/forward-filled prices.

#### Scenario: Missing CSI 300 price fails before artifacts
- **WHEN** `SSE:510300` lacks a price on an official session in the requested range
- **THEN** the backtest fails with the ETF identity and missing date
- **AND** it persists no signal, run, strategy curve, benchmark, or benchmark curve from that attempt

#### Scenario: Complete benchmark inputs share strategy dates
- **WHEN** every strategy and benchmark ETF/session resolves
- **THEN** each benchmark curve has one point for every strategy curve date

#### Scenario: Unexplained CSI 300 gap fails before artifacts
- **WHEN** listed `SSE:510300` has neither price nor authoritative status on a requested session
- **THEN** the backtest fails with ETF/date context and persists no attempted artifact

#### Scenario: Confirmed CSI 300 non-trading session resolves
- **WHEN** `SSE:510300` has authoritative full-day status and a prior resolved value
- **THEN** its benchmark curve retains that official session with unchanged adjusted valuation

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

### Requirement: Fixed benchmarks expose regime-specific comparison metrics
Every newly calculated benchmark-enabled backtest SHALL retain monthly geometric-mean Up Capture, Down Capture, and their selected-month counts separately for `equal_weight_monthly` and `csi_300_buy_hold`. The CSI 300 comparison SHALL additionally retain proxy-qualified annualized CAPM Alpha, Beta, R-squared, and CAPM observation count, while equal-weight CAPM fields SHALL remain null and its monthly capture fields remain independently calculable.

#### Scenario: New dual-benchmark result retains correct metric ownership
- **WHEN** a benchmark-enabled run completes with calculable regime metrics
- **THEN** both benchmark children retain their own monthly up/down capture values and selected-month counts
- **AND** only the CSI 300 child retains CAPM proxy-regression values and count

#### Scenario: Existing comparison metrics remain unchanged
- **WHEN** benchmark-regime metrics are added to a completed run
- **THEN** existing benchmark return, risk, TE, IR, curve, cost, identity, and strict-date semantics remain unchanged

### Requirement: Fixed benchmark curves expose matching stability series
Backtest Detail stability derivation SHALL process each persisted fixed benchmark curve using the same validation, adjacent-net-value return reconstruction, 63-session rolling, calendar grouping, requested-scope partial flag, risk-free-rate input, precision, and ordering rules as the strategy. Benchmark identity and result ownership SHALL remain explicit.

#### Scenario: Strategy and benchmark use identical derivation rules
- **WHEN** strategy and one benchmark have identical persisted curve values and dates
- **THEN** their rolling and calendar stability values are identical
- **AND** remain attached to their separate entity identities

#### Scenario: Legacy run has no fabricated benchmark series
- **WHEN** a legacy backtest has no benchmark children
- **THEN** strategy stability remains available when its curve is valid
- **AND** the benchmark stability collection is empty

### Requirement: Fixed benchmarks retain absolute distribution-risk metrics
Each newly calculated fixed benchmark SHALL retain its own Historical VaR 95%, Historical CVaR 95%, Skewness, Excess Kurtosis, effective observation count, and tail observation count using exactly the same effective-return, threshold, rank, sign, correction, precision, and version semantics as the strategy.

#### Scenario: Identical strategy and benchmark returns produce identical metrics
- **WHEN** the strategy and one fixed benchmark have identical effective return sequences
- **THEN** their distribution metrics and counts are identical
- **AND** remain persisted on their separate curve owners

#### Scenario: Existing relative metrics remain unchanged
- **WHEN** distribution-risk metrics are calculated for fixed benchmarks
- **THEN** return, drawdown, Volatility, Sharpe, Sortino, Calmar, duration, TE/IR, CAPM/capture, cost, curve, and identity semantics remain unchanged


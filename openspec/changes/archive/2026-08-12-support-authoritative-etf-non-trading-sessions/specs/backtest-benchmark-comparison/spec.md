## MODIFIED Requirements

### Requirement: Benchmark trading and valuation semantics
Both benchmarks SHALL use the shared resolved official-session panel. They SHALL initialize at the first session on which their complete target is executable without entry cost and SHALL value holdings by resolved adjusted-value ratios. A confirmed full-day non-trading holding SHALL retain unchanged adjusted value and remain non-tradable. Equal-weight monthly targets SHALL arise only on the existing schedule, use configured transaction costs, and defer atomically when any changed leg is non-tradable; a newer scheduled target replaces an older pending target. CSI 300 SHALL remain buy-and-hold after its initial executable allocation.

#### Scenario: Initial allocation does not charge cost
- **WHEN** either benchmark's initial target contains only tradable legs
- **THEN** it initializes without transaction cost

#### Scenario: Blocked initial allocation remains cash
- **WHEN** an initial benchmark target includes a non-tradable ETF
- **THEN** the complete target remains pending and the benchmark remains cash

#### Scenario: Monthly equal-weight rebalance charges cost
- **WHEN** a scheduled equal-weight target becomes wholly tradable after being immediately executable or deferred
- **THEN** it executes all changed legs once and charges configured cost against turnover once

#### Scenario: New monthly target replaces pending target
- **WHEN** another scheduled equal-weight target occurs before the prior target executes
- **THEN** the newer complete target replaces the pending target

#### Scenario: CSI 300 has no later rebalance
- **WHEN** CSI 300 advances after initial allocation
- **THEN** it changes only through resolved `SSE:510300` valuation
- **AND** incurs no later transaction cost

#### Scenario: Confirmed non-trading benchmark session is explicit
- **WHEN** a benchmark holding has authoritative full-day non-trading status
- **THEN** that session contributes an unchanged adjusted valuation and remains present in the curve

### Requirement: Benchmark input completeness
Benchmark-enabled backtests SHALL use the strategy's identical ordered official-session axis and shared resolver. They MUST require a unique listed active `SSE:510300` identity and exactly one admissible source state for every required benchmark ETF/session. Unknown gaps, absent listing metadata, conflicts, and missing carry anchors MUST fail before artifacts; confirmed full-day status MAY resolve through the shared non-trading policy. The system MUST NOT shorten a series, infer a status, or create raw zero/forward-filled prices.

#### Scenario: Unexplained CSI 300 gap fails before artifacts
- **WHEN** listed `SSE:510300` has neither price nor authoritative status on a requested session
- **THEN** the backtest fails with ETF/date context and persists no attempted artifact

#### Scenario: Confirmed CSI 300 non-trading session resolves
- **WHEN** `SSE:510300` has authoritative full-day status and a prior resolved value
- **THEN** its benchmark curve retains that official session with unchanged adjusted valuation

#### Scenario: Complete benchmark inputs share strategy dates
- **WHEN** every strategy and benchmark ETF/session resolves
- **THEN** each benchmark curve has one point for every strategy curve date

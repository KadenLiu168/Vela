## ADDED Requirements

### Requirement: Backtest Detail presents proxy CAPM and capture evidence
Backtest Detail SHALL show Monthly Up Capture and Monthly Down Capture with selected-month counts inside both named benchmark groups. It SHALL show annualized Alpha, Beta, R-squared, and daily CAPM observation count only in the CSI 300 group, label Alpha as `CSI 300 ETF proxy Alpha (252D compounded)` or semantically equivalent text, label capture as a non-annualized monthly geometric ratio, and never present equal-weight results as CAPM.

#### Scenario: New detail distinguishes benchmark meanings
- **WHEN** a benchmark-enabled detail response contains calculable benchmark-regime metrics
- **THEN** both benchmark groups display their own monthly capture ratios and selected-month counts
- **AND** only the CSI 300 group displays proxy-qualified CAPM fields

#### Scenario: Null evidence is not fabricated
- **WHEN** a new field is null for a legacy or mathematically undefined result
- **THEN** the UI renders the established unavailable placeholder and available observation count
- **AND** does not display zero, NaN, Infinity, or a synthetic ratio

### Requirement: Walk-forward Detail presents regime aggregates as evidence
Walk-forward Detail SHALL display per-window and aggregate proxy Alpha/Beta/R-squared and named-benchmark monthly capture evidence with explicit daily-session versus selected-month count units, metric-local valid counts, and `insufficient_evidence`. It SHALL preserve existing evidence, navigation, and terminal states and SHALL NOT add a score, threshold, ranking, or pass/fail result.

#### Scenario: Evidence statuses remain metric-local
- **WHEN** a Walk-forward response contains different valid counts across regime metrics
- **THEN** each displayed aggregate uses its own count and status
- **AND** existing OOS, benchmark, generalization, parameter, and navigation evidence remains available

### Requirement: Expanded metric groups remain accessible and responsive
The added Backtest and Walk-forward content SHALL use semantic headings/labels, expose benchmark identity and observation counts to assistive technology, support keyboard access, and avoid page-level horizontal overflow at the project's required 1440x1000 and 390x844 viewports.

#### Scenario: Desktop and narrow layouts preserve meaning
- **WHEN** the expanded detail pages render at both required viewports
- **THEN** proxy and benchmark group ownership remains visually and programmatically clear
- **AND** all existing actions remain reachable without page-level horizontal overflow

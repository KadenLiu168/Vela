## ADDED Requirements

### Requirement: Fixed benchmarks expose regime-specific comparison metrics
Every newly calculated benchmark-enabled backtest SHALL retain monthly geometric-mean Up Capture, Down Capture, and their selected-month counts separately for `equal_weight_monthly` and `csi_300_buy_hold`. The CSI 300 comparison SHALL additionally retain proxy-qualified annualized CAPM Alpha, Beta, R-squared, and CAPM observation count, while equal-weight CAPM fields SHALL remain null and its monthly capture fields remain independently calculable.

#### Scenario: New dual-benchmark result retains correct metric ownership
- **WHEN** a benchmark-enabled run completes with calculable regime metrics
- **THEN** both benchmark children retain their own monthly up/down capture values and selected-month counts
- **AND** only the CSI 300 child retains CAPM proxy-regression values and count

#### Scenario: Existing comparison metrics remain unchanged
- **WHEN** benchmark-regime metrics are added to a completed run
- **THEN** existing benchmark return, risk, TE, IR, curve, cost, identity, and strict-date semantics remain unchanged

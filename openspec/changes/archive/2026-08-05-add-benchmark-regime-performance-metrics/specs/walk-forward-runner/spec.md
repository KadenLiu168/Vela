## ADDED Requirements

### Requirement: Walk-forward reports benchmark-regime evidence per window
Every selected OOS window SHALL retain the persisted daily CAPM proxy result for `csi_300_buy_hold` and monthly geometric-capture results for both fixed benchmarks, including their local selected-month counts and null states. The terminal evidence report SHALL identify the benchmark, proxy, monthly ratio, and count-unit semantics and SHALL NOT recalculate values from a stitched curve.

#### Scenario: Selected windows retain named comparison evidence
- **WHEN** a Walk-forward run selects multiple successful OOS backtests
- **THEN** each window reports its CSI 300 proxy Alpha/Beta/R-squared evidence
- **AND** reports separate up/down capture evidence for both fixed benchmarks

### Requirement: Walk-forward aggregates regime metrics without a verdict
The report SHALL aggregate each CAPM Alpha, Beta, R-squared, Up Capture, and Down Capture series independently using the existing mean, median, minimum, maximum, population standard deviation, total-window count, valid contributing count, and evidence-status contract. Null values SHALL not contribute, zero values SHALL remain valid, and the report SHALL NOT emit thresholds, rankings, or pass/fail decisions.

#### Scenario: Metric-local valid counts differ
- **WHEN** some windows lack a calculable down regime while retaining calculable CAPM and up-regime values
- **THEN** every aggregate exposes its own valid count and `insufficient_evidence` status
- **AND** no missing value is replaced with zero

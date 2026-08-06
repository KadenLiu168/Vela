## ADDED Requirements

### Requirement: Walk-forward retains per-window distribution evidence
Every selected OOS window SHALL retain persisted strategy and fixed-benchmark Historical VaR, Historical CVaR, Skewness, Excess Kurtosis, effective count, tail count, and derived evidence status from its owned records. The report SHALL identify one-day historical positive-loss and excess-kurtosis semantics and MUST NOT recalculate metrics from a stitched curve.

#### Scenario: Selected OOS window reports every curve owner
- **WHEN** a Walk-forward run selects a successful OOS backtest with both fixed benchmarks
- **THEN** the window reports separate strategy, equal-weight, and CSI 300 distribution evidence and counts

### Requirement: Walk-forward aggregates distribution evidence without a verdict
The report SHALL aggregate each entity's four distribution metrics separately using mean, median, minimum, maximum, population standard deviation, total-window count, valid contributing count, and evidence status. It SHALL identify these values as descriptive statistics across independent per-window metric estimates rather than VaR/CVaR or shape statistics calculated from a combined or stitched return distribution. Nulls SHALL not contribute, valid zeros SHALL contribute, and minimum/maximum SHALL not be relabeled as a universal best/worst judgment across signed shape and positive-loss metrics.

#### Scenario: Insufficient windows remain metric-local
- **WHEN** some selected windows have fewer than 100 effective observations or constant distributions
- **THEN** every entity/metric aggregate exposes its own valid count and `insufficient_evidence`
- **AND** no null is replaced with zero and no pass/fail result is emitted

#### Scenario: Aggregate labels preserve the window-level interpretation
- **WHEN** the report presents a mean, median, range, or population standard deviation for per-window VaR, CVaR, Skewness, or Excess Kurtosis
- **THEN** it identifies the result as a statistic across independent window estimates
- **AND** does not describe it as a risk value calculated from a combined strategy return distribution

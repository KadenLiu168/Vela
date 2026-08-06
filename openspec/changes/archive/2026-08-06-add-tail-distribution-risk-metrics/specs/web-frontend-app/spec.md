## ADDED Requirements

### Requirement: Backtest Detail presents historical distribution risk explicitly
Backtest Detail SHALL present strategy and each fixed benchmark's `Historical VaR 95% (1D loss)`, `Historical CVaR 95% (1D loss)`, `Skewness`, and `Excess kurtosis (normal = 0)` with effective/tail observation counts and evidence status. It SHALL use exact API values, show positive losses as loss magnitudes, distinguish insufficient/legacy/undefined nulls, and make no forecast or regulatory-capital claim. When evidence is insufficient, it SHALL explain that a displayed tail count is the cardinality implied by the fixed 5% rank rule while publication of the metrics still requires at least 100 effective observations.

#### Scenario: Sufficient evidence displays exact semantics
- **WHEN** a detail response contains sufficient calculable distribution metrics
- **THEN** each owning group displays exact API values, counts, confidence, horizon, historical method, and excess-kurtosis baseline

#### Scenario: Null reason remains visible
- **WHEN** metrics are null because evidence is insufficient, history is legacy, or distribution shape is constant
- **THEN** the UI presents the corresponding unavailable explanation and available counts
- **AND** does not display zero, NaN, Infinity, a threshold verdict, or a fabricated metric

#### Scenario: Insufficient tail count does not imply a published metric
- **WHEN** a detail response contains 99 effective observations, a tail count of 5, and null distribution metrics
- **THEN** the UI identifies the five observations as the fixed-rank tail cardinality
- **AND** explains that the metrics remain unavailable because the 100-observation publication requirement is not met

### Requirement: Walk-forward Detail presents distribution evidence without scoring
Walk-forward Detail SHALL display per-window and aggregate strategy/fixed-benchmark distribution evidence from v3 with metric-local valid counts and statuses, preserve all existing v2 and stitched-OOS content, and SHALL NOT add scoring, ranking, alerts, or pass/fail conclusions. It SHALL label aggregate values as descriptive statistics across independent per-window metric estimates and MUST NOT present them as VaR/CVaR or shape statistics of a combined or stitched strategy return distribution.

#### Scenario: Mixed evidence remains owner and metric specific
- **WHEN** v3 contains different valid counts across owners and metrics
- **THEN** each displayed aggregate retains its own owner, count, nulls, and status
- **AND** existing benchmark-regime, OOS, generalization, parameter, stitched, and navigation evidence remains available

#### Scenario: Aggregate explanation rejects a combined-distribution interpretation
- **WHEN** Walk-forward Detail displays aggregate VaR, CVaR, Skewness, or Excess Kurtosis evidence
- **THEN** the aggregate section explains that it summarizes independent window estimates
- **AND** does not claim to measure the tail or shape of one combined strategy return distribution

### Requirement: Expanded risk groups remain accessible and responsive
The added Backtest and Walk-forward risk content SHALL use semantic headings/labels, expose counts/statuses to assistive technology, retain keyboard access and existing actions, and avoid page-level horizontal overflow at 1440x1000 and 390x844.

#### Scenario: Required viewports preserve risk meaning
- **WHEN** the expanded pages render at either required viewport
- **THEN** strategy/benchmark ownership, historical loss semantics, counts, and null states remain readable and programmatically clear
- **AND** no existing action becomes unreachable or causes page-level horizontal overflow

## ADDED Requirements

### Requirement: Distribution evidence requires 100 effective returns
The system SHALL exclude the initial placeholder return and retain the count of effective daily returns. It SHALL publish `sufficient` distribution evidence only when the count is at least 100; otherwise Historical VaR 95%, Historical CVaR 95%, Skewness, and Excess Kurtosis SHALL all be null with `insufficient_evidence`. Tail observation count SHALL equal `ceil(0.05 * observation_count)`, including zero for no observations.

#### Scenario: Ninety-nine observations are insufficient
- **WHEN** a curve has 99 effective daily returns
- **THEN** all four distribution metrics are null
- **AND** observation count is 99, tail count is 5, and evidence status is `insufficient_evidence`

#### Scenario: One hundred observations are sufficient
- **WHEN** a curve has 100 effective daily returns
- **THEN** the historical tail contains exactly 5 observations
- **AND** calculable metrics are published with `sufficient` evidence

### Requirement: Historical VaR and CVaR use fixed nearest-rank loss semantics
For sufficient evidence of size `n`, the system SHALL sort unquantized daily returns ascending, set `tail_count = ceil(0.05*n)`, use the return at index `tail_count - 1` as the 95% VaR cutoff, and use exactly the first `tail_count` returns for CVaR. It SHALL publish `max(0, -cutoff_return)` as `historical_var_95` and `max(0, -mean(tail_returns))` as `historical_cvar_95`, quantizing only final values to six places.

#### Scenario: Controlled 100-return tail has an independent oracle
- **WHEN** 100 controlled returns have five independently known worst observations
- **THEN** VaR equals the positive loss magnitude of the fifth-worst return
- **AND** CVaR equals the positive loss magnitude of the unquantized mean of exactly the five worst returns

#### Scenario: All sufficient returns are non-negative
- **WHEN** at least 100 effective returns are all zero or positive
- **THEN** VaR and CVaR are both `0.000000`

#### Scenario: Tail loss invariant holds
- **WHEN** sufficient evidence produces historical loss metrics
- **THEN** `historical_cvar_95 >= historical_var_95 >= 0`

### Requirement: Return shape uses bias-corrected Fisher statistics
For sufficient evidence with non-zero second central moment, the system SHALL calculate adjusted Fisher-Pearson sample Skewness as `sqrt(n(n-1))/(n-2) * m3/m2^(3/2)` and bias-corrected Fisher excess Kurtosis as `(n-1)/((n-2)(n-3)) * ((n+1)*(m4/m2^2 - 3) + 6)`, retaining unquantized population central moments and quantizing final values to six places. Excess Kurtosis SHALL be labeled with normal-distribution baseline zero.

#### Scenario: Controlled asymmetric distribution has an independent oracle
- **WHEN** at least 100 controlled returns have independently calculated non-zero moments
- **THEN** published Skewness and Excess Kurtosis equal the bias-corrected six-decimal oracle values

#### Scenario: Constant sufficient distribution has undefined shape
- **WHEN** at least 100 effective returns are identical
- **THEN** Skewness and Excess Kurtosis are null
- **AND** VaR/CVaR and sufficient evidence status remain governed by their own rules

### Requirement: Tail-distribution calculation is additive and versioned
The `vela_core` package SHALL publicly export an immutable result type and one shared tail-distribution calculation function used by strategy and benchmark execution. Every calculation snapshot SHALL record `tail_distribution_metric_version: tail_distribution_metrics_v1`; persisted values/counts SHALL be quantized or typed exactly once and reports/routers/browsers MUST NOT recompute them.

#### Scenario: Public calculation matches execution
- **WHEN** the public function receives the same points used by backtest execution
- **THEN** it returns the same immutable values, counts, and evidence status that execution persists or retains in isolation
- **AND** the snapshot records `tail_distribution_metrics_v1`

### Requirement: Tail metrics remain per authoritative curve
The system MUST NOT calculate VaR, CVaR, Skewness, or Excess Kurtosis across stitched Walk-forward OOS reset boundaries. Normal runs, selected OOS runs, benchmarks, and isolated training trials SHALL use only their own authoritative point sequences.

#### Scenario: Stitched OOS does not create a distribution
- **WHEN** a Walk-forward history exposes an available stitched curve
- **THEN** no parent-level distribution metric is calculated from that curve
- **AND** per-window metrics remain owned by referenced OOS runs and benchmarks

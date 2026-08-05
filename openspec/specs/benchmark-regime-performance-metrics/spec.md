# benchmark-regime-performance-metrics Specification

## Purpose
Defines CAPM proxy-regression and monthly up/down capture calculation semantics for benchmark-enabled backtests, including strict date alignment, benchmark-defined regime classification, fail-closed behavior, and additive versioned persistence.

## Requirements

### Requirement: CAPM proxy regression uses aligned excess daily returns
For strategy and `csi_300_buy_hold` curves with identical ordered effective dates, the system SHALL subtract `risk_free_rate / 252` from both daily return series, calculate Beta from unquantized population covariance divided by unquantized market-proxy population variance, calculate daily Alpha as mean strategy excess return minus Beta times mean proxy excess return, and publish Alpha as `(1 + daily_alpha)^252 - 1`. It SHALL publish Beta, annualized Alpha, R-squared, and effective observation count, quantizing only final Decimal metrics to six places and labeling Alpha as a 252-session compounded result against the CSI 300 ETF proxy.

#### Scenario: Controlled proxy vector has an independent oracle
- **WHEN** aligned strategy and CSI 300 proxy returns plus a fixed annual risk-free rate produce non-zero strategy and proxy variances
- **THEN** Alpha, Beta, and R-squared equal independently hand-derived six-decimal values
- **AND** the observation count equals the number of aligned effective dates

#### Scenario: Regression evidence is mathematically undefined
- **WHEN** fewer than two aligned effective observations exist or proxy excess-return variance is zero
- **THEN** Alpha, Beta, and R-squared are null
- **AND** the available observation count remains explicit

#### Scenario: Constant strategy has no defined fit strength
- **WHEN** strategy excess returns are constant and proxy excess returns have non-zero variance
- **THEN** Beta remains calculable
- **AND** R-squared is null because strategy variance is zero

### Requirement: CAPM semantics are restricted to the market proxy
The system SHALL calculate CAPM fields only for the fixed `csi_300_buy_hold` benchmark and SHALL NOT describe `equal_weight_monthly` as a market factor or publish Alpha, Beta, R-squared, or a CAPM observation count for it.

#### Scenario: Equal-weight comparison has no fabricated CAPM
- **WHEN** a benchmark-enabled backtest contains the fixed equal-weight comparison
- **THEN** all CAPM fields for that benchmark are null
- **AND** its capture metrics remain independently available when calculable

### Requirement: Up and Down Capture use benchmark-defined regimes
For each fixed benchmark, the system SHALL first group the strictly aligned strategy and benchmark daily returns by identical chronological calendar `(year, month)` keys and calculate each observed monthly bucket as `product(1 + daily_return) - 1`. It SHALL retain a first or last partial calendar month using only that run's aligned observations and SHALL NOT fill, infer, or fetch returns outside the owned interval. It SHALL select monthly buckets with benchmark monthly return strictly greater than zero for the up regime and strictly less than zero for the down regime, excluding benchmark zero-return months. Within each regime of `n` selected months, it SHALL calculate strategy and benchmark geometric mean monthly returns as `product(1 + selected_monthly_return)^(1/n) - 1` and publish their ratio without annualization, retaining unquantized intermediates and quantizing only the final ratio to six places.

#### Scenario: Controlled monthly regimes compound independently
- **WHEN** aligned daily observations form positive, negative, and zero benchmark calendar-month returns
- **THEN** Up Capture uses only positive-benchmark month buckets
- **AND** Down Capture uses only negative-benchmark month buckets
- **AND** zero-benchmark months contribute to neither selected-month count nor ratio
- **AND** no `252/n` or other annualization factor is applied

#### Scenario: Partial edge months remain owned evidence
- **WHEN** an aligned run begins or ends inside a calendar month
- **THEN** the observed daily returns in that edge month form one chronological monthly bucket
- **AND** neither strategy nor benchmark receives a return outside the aligned run interval

#### Scenario: Regime ratio is undefined
- **WHEN** a monthly regime has no selected buckets or a selected bucket contains a constituent daily return or resulting monthly return at or below `-1`
- **THEN** that capture ratio is null
- **AND** its actual selected calendar-month count remains explicit

#### Scenario: Valid benchmark regime denominator is non-zero
- **WHEN** a nonempty up or down regime contains only valid monthly returns
- **THEN** its benchmark geometric mean retains the selected regime's strict sign before final quantization
- **AND** a near-zero non-zero denominator is neither rounded early nor replaced with null

### Requirement: Benchmark comparison dates fail closed
The calculation SHALL exclude each curve's initial placeholder point and require identical effective-date values and order before calculating CAPM or capture metrics. It MUST NOT intersect, sort, shorten, forward-fill, or zero-fill either series.

#### Scenario: Strategy and benchmark dates differ
- **WHEN** effective strategy and benchmark dates differ in value or order
- **THEN** benchmark-regime calculation fails instead of returning partial metrics

### Requirement: Benchmark-regime calculation is additive and versioned
The `vela_core` package SHALL publicly export an immutable benchmark-regime result type and its shared calculation function. Every benchmark-enabled run that reaches this calculation SHALL record `benchmark_regime_metric_version: benchmark_regime_metrics_v1` and the exact annual risk-free-rate input in its parameter snapshot; benchmark-skipping training trials SHALL calculate neither the family nor its version marker.

#### Scenario: Public calculation matches persisted execution
- **WHEN** a caller imports and evaluates the public calculation function with the same curves used by a completed benchmark-enabled backtest
- **THEN** it resolves to the implementation used by execution and persistence
- **AND** the run snapshot records `benchmark_regime_metrics_v1`

#### Scenario: Training trial remains benchmark-free
- **WHEN** Walk-forward parameter search runs a benchmark-skipping isolated training trial
- **THEN** it creates no benchmark-regime result or version marker in the source database

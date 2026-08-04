## ADDED Requirements

### Requirement: Sortino uses risk-free MAR and daily downside deviation
The system SHALL calculate Sortino from effective daily returns after the initial placeholder. It SHALL use `risk_free_rate / 252` as daily MAR, calculate each downside observation as `min(daily_return - daily_MAR, 0)`, calculate annualized downside deviation as `sqrt(mean(downside_observation^2)) * sqrt(252)` across all effective observations, and return `mean(daily_return - daily_MAR) * 252 / annualized_downside_deviation`. All intermediate values SHALL remain unquantized and only the final Sortino SHALL be quantized to six decimal places.

#### Scenario: Controlled downside observations
- **WHEN** at least two effective returns include observations below the daily MAR and have non-zero downside deviation
- **THEN** Sortino uses all effective observations in the lower-partial-moment denominator
- **AND** returns the six-decimal annualized excess-return ratio

#### Scenario: Controlled Sortino vector has an independent oracle
- **WHEN** annual `risk_free_rate` is `0.0252` and effective daily returns are `[0.0101, -0.0049, 0.0201]`
- **THEN** daily excess returns are `[0.0100, -0.0050, 0.0200]`
- **AND** Sortino is `45.825757`

#### Scenario: No downside dispersion
- **WHEN** fewer than two effective observations exist or every effective return is at least the daily MAR
- **THEN** Sortino is null

### Requirement: Calmar uses calendar CAGR and absolute maximum drawdown
The system SHALL calculate Calmar as the existing published six-decimal calendar-time CAGR divided by the absolute value of the existing published six-decimal negative maximum drawdown. It MUST NOT recalculate either input from the curve or replace CAGR with a 252-session return. The division SHALL remain unquantized until final Calmar is quantized to six decimal places.

#### Scenario: Positive CAGR with negative drawdown
- **WHEN** CAGR is `0.12` and maximum drawdown is `-0.08`
- **THEN** Calmar is `1.500000`

#### Scenario: Calmar is undefined without a denominator
- **WHEN** CAGR is null or maximum drawdown is zero
- **THEN** Calmar is null

#### Scenario: Negative CAGR remains negative
- **WHEN** CAGR is negative and maximum drawdown is non-zero
- **THEN** Calmar is negative

### Requirement: Longest drawdown duration uses official-session intervals
The system SHALL identify every interval beginning at a high-water peak and ending at the first later official-session point whose net value is at least that peak, or at the final point if unrecovered. While not underwater, a point equal to the current high-water value SHALL replace the peak anchor, and an equal-value recovery point SHALL anchor any following interval. Duration SHALL equal the end index minus the peak index. The result SHALL retain duration sessions, peak date, earliest deepest trough date, and a null recovery date for an ongoing interval. The longest interval SHALL win, with ties resolved by earliest peak then earliest trough.

#### Scenario: Completed drawdown recovers
- **WHEN** a peak is followed by underwater points and a later point reaches the peak net value
- **THEN** duration is the number of official-session index intervals from peak through recovery
- **AND** peak, earliest deepest trough and recovery dates are returned

#### Scenario: Ongoing drawdown ends at the backtest boundary
- **WHEN** the final point remains below its preceding high-water mark
- **THEN** duration ends at the final point
- **AND** recovery date is null

#### Scenario: Curve never goes underwater
- **WHEN** a curve is flat or monotonically rising
- **THEN** duration is zero
- **AND** peak, trough and recovery dates are null

#### Scenario: Last equal high anchors the next drawdown
- **WHEN** four ordered official-session net values are `[1.0@d1, 1.0@d2, 0.9@d3, 1.0@d4]`
- **THEN** the longest interval has peak `d2`, trough `d3`, recovery `d4`, and duration `2`

### Requirement: Tracking Error and Information Ratio use aligned active returns
For a strategy and benchmark with identical ordered effective dates, the system SHALL calculate `active_return = strategy_daily_return - benchmark_daily_return`, raw Tracking Error as population standard deviation of active returns multiplied by `sqrt(252)`, and Information Ratio as `mean(active_return) * 252 / raw Tracking Error`. All intermediate values SHALL remain unquantized and final Decimal fields SHALL be quantized to six places. Information Ratio MUST NOT use the quantized Tracking Error field as its denominator. If published Tracking Error quantizes to `0.000000`, Information Ratio SHALL be null.

#### Scenario: Active returns have dispersion
- **WHEN** at least two aligned active-return observations have non-zero population standard deviation
- **THEN** the system returns six-decimal Tracking Error and Information Ratio

#### Scenario: Controlled active-return vector has an independent oracle
- **WHEN** aligned active returns are `[0.002, -0.001, 0.005]`
- **THEN** Tracking Error is `0.038884`
- **AND** Information Ratio is `12.961481`, calculated from the unquantized annualized Tracking Error rather than the published six-decimal field

#### Scenario: Active returns have zero dispersion
- **WHEN** at least two aligned active returns are equal
- **THEN** Tracking Error is `0.000000`
- **AND** Information Ratio is null

#### Scenario: Active returns are insufficient
- **WHEN** fewer than two aligned effective active-return observations exist
- **THEN** Tracking Error and Information Ratio are null

#### Scenario: Tracking Error is below public precision
- **WHEN** raw annualized Tracking Error is non-zero but quantizes to `0.000000`
- **THEN** published Tracking Error is `0.000000`
- **AND** Information Ratio is null

#### Scenario: Active dates do not match
- **WHEN** strategy and benchmark effective dates differ in value or order
- **THEN** calculation fails instead of intersecting, shortening or filling either series

### Requirement: Performance metric version is auditable
Every backtest that reaches expanded strategy metric calculation SHALL record `performance_metric_version` equal to `performance_metrics_v1` in its parameter snapshot together with the exact risk-free-rate value used by Sharpe and Sortino. This includes normal success and partial runs, selected Walk-forward OOS runs, and benchmark-skipping training trials; training records SHALL remain confined to their isolated snapshot.

#### Scenario: New run records metric semantics
- **WHEN** a backtest completes with the expanded metric set
- **THEN** its parameter snapshot contains `performance_metric_version: performance_metrics_v1`
- **AND** retains the exact annual risk-free-rate input

#### Scenario: Partial run records calculated semantics
- **WHEN** a normal backtest reaches expanded metric calculation and completes with `partial` status
- **THEN** its parameter snapshot records `performance_metrics_v1` and the exact annual risk-free-rate input

#### Scenario: Training trial is versioned only in isolation
- **WHEN** a Walk-forward training trial skips benchmark calculation
- **THEN** it calculates and versions the strategy expanded metrics in the isolated training snapshot
- **AND** it writes no training run or metric to the source database

### Requirement: Expanded metric calculation API is additive
The `vela_core` package SHALL publicly export immutable `StrategySortinoRatio`, `StrategyCalmarRatio`, `StrategyLongestDrawdownDuration`, and `ActiveRiskMetrics` result types together with `calculate_strategy_sortino_ratio(points, *, risk_free_rate)`, `calculate_strategy_calmar_ratio(annualized_return, maximum_drawdown)`, `calculate_strategy_longest_drawdown_duration(points)`, and `calculate_active_risk_metrics(strategy_points, benchmark_points)`. Each function SHALL return its matching immutable result type. Existing public metric types, functions and signatures MUST remain unchanged.

#### Scenario: Public imports expose the shared calculation path
- **WHEN** a Python caller imports the expanded result types and calculation functions from `vela_core`
- **THEN** every named import resolves to the same implementation used by strategy and benchmark calculations
- **AND** existing performance-metric imports remain compatible

## ADDED Requirements

### Requirement: OOS evidence sufficiency
Every OOS metric summary and rate SHALL expose its total window count, valid contributing count, and an evidence status. Evidence status SHALL be `sufficient` only when at least three windows contribute a valid value and SHALL otherwise be `insufficient_evidence`. The status SHALL represent only this minimum-count threshold and MUST NOT imply window independence, statistical adequacy or strategy validity. Insufficient evidence MUST NOT prevent the report from being generated and MUST NOT be converted into an automatic strategy pass or failure.

#### Scenario: Two valid windows remain reportable
- **WHEN** a Walk-forward run has two valid OOS total-return observations
- **THEN** the report includes their statistics and counts
- **AND** marks the total-return evidence `insufficient_evidence`
- **AND** does not emit a strategy pass or failure decision

#### Scenario: Null is local to one metric
- **WHEN** one window has null Sharpe but valid total return and maximum drawdown
- **THEN** that window is excluded only from the Sharpe valid count
- **AND** still contributes to the total-return and maximum-drawdown summaries

#### Scenario: No valid observations remain explicit
- **WHEN** an OOS metric has no valid observation
- **THEN** its descriptive statistics are null, total and zero-valid counts remain visible, and evidence is `insufficient_evidence`

### Requirement: OOS positive and benchmark-win rates
The report SHALL calculate the OOS positive-window rate from non-null strategy total returns strictly greater than zero. For each fixed benchmark it SHALL calculate an outperformance rate from non-null strategy-minus-benchmark total-return differences strictly greater than zero. Every rate SHALL expose its numerator, denominator, value, total window count, valid contributing count and evidence status; zero differences SHALL count as ties rather than wins. A rate with no valid value SHALL expose numerator zero, denominator zero, null value and `insufficient_evidence`.

#### Scenario: Positive and tied windows have distinct treatment
- **WHEN** three OOS total returns are positive, zero and negative
- **THEN** the positive-window numerator is one and the denominator is three
- **AND** the zero-return window is not counted as positive

#### Scenario: Benchmark win rates remain separate
- **WHEN** the strategy beats the equal-weight benchmark in two valid windows and the CSI 300 benchmark in one valid window
- **THEN** the report exposes separate outperformance rates and counts for both benchmark keys

### Requirement: IS to OOS Sharpe generalization evidence
For every window with non-null train and OOS Sharpe, the report SHALL calculate `train_sharpe - oos_sharpe` and aggregate the valid gaps using mean, median, minimum, maximum, population standard deviation and evidence counts. It MUST NOT derive an IS/OOS Sharpe ratio.

#### Scenario: Positive gap represents degradation
- **WHEN** a window has train Sharpe `1.2` and OOS Sharpe `0.5`
- **THEN** its generalization gap is `0.7`

#### Scenario: Null OOS Sharpe is excluded locally
- **WHEN** a window has valid train Sharpe and null OOS Sharpe
- **THEN** it does not contribute to the generalization-gap summary
- **AND** remains available to other metric summaries

### Requirement: Quantified parameter stability
For every searched parameter, the report SHALL resolve the selected dot-path from the validated strategy configuration's JSON-mode data, list frequencies keyed by that effective value's canonical JSON, and compare chronologically adjacent windows to produce a transition count, comparison count and transition rate. It MUST NOT treat parameter-generator Python representation differences as effective configuration changes. A parameter with fewer than two comparable windows SHALL have no transition rate.

#### Scenario: One change across three windows
- **WHEN** one parameter has values `60`, `60`, and `120` in three chronological windows
- **THEN** its value frequencies are `60: 2` and `120: 1`
- **AND** its transition count is one across two comparisons
- **AND** its transition rate is `0.5`

### Requirement: OOS windows remain isolated evidence
The Walk-forward report SHALL treat each OOS backtest as an independent evaluation interval and MUST NOT concatenate or link their equity curves, compute cross-window path metrics, or represent them as one continuously tradable portfolio.

#### Scenario: Adjacent windows do not create a continuous curve
- **WHEN** one OOS window ends immediately before the next OOS window starts
- **THEN** the report retains both window results separately
- **AND** does not synthesize a boundary return or continuous OOS net-value series

## MODIFIED Requirements

### Requirement: Walk-forward orchestration
The system SHALL, for each window, search the parameter space on the training period, select the best parameter combination by `sharpe_ratio`, evaluate it on the test period, and aggregate results across all windows. Only successful training runs with a non-null Sharpe SHALL be eligible. Highest Sharpe SHALL win; equal values SHALL be resolved by the lexicographic order of each combination's canonical JSON representation. Every selected OOS result SHALL retain total return, annualized return, maximum drawdown, volatility and Sharpe.

#### Scenario: Single window with parameter search
- **WHEN** a walk-forward run is configured with one window and a parameter space of 2 combinations
- **THEN** the system runs exactly 2 training backtests, selects the best by Sharpe, and runs exactly 1 OOS backtest
- **AND** the window result contains the best parameters and all five OOS metrics

#### Scenario: Multiple windows aggregate OOS results
- **WHEN** a walk-forward run completes 3 windows
- **THEN** the aggregate report includes mean, median, minimum, maximum, population standard deviation, total window count and valid count for each of the five non-null OOS metrics
- **AND** labels the minimum maximum-drawdown value as the worst drawdown because maximum drawdown uses the negative-number convention

#### Scenario: Equal training Sharpe is deterministic
- **WHEN** two eligible combinations have the same highest training Sharpe
- **THEN** the system selects the combination whose canonical JSON sorts first

### Requirement: Source writes use the caller transaction
The walk-forward runner SHALL neither commit nor roll back the caller-provided source session. The CLI SHALL execute the complete run inside the repository's managed-session boundary so all selected OOS runs and their fixed benchmark results commit only after every window succeeds and all writes from the command roll back if any later OOS or fixed benchmark evaluation fails.

#### Scenario: Complete run commits source outputs
- **WHEN** all windows, OOS evaluations, and fixed benchmark evaluations succeed through the CLI
- **THEN** the managed caller transaction commits all source-side outputs once

#### Scenario: Later window failure rolls back source outputs
- **WHEN** a later OOS or fixed benchmark evaluation fails after an earlier window added source-side rows
- **THEN** the CLI exits non-zero and the managed caller transaction persists none of this command's source-side rows

### Requirement: OOS dual-benchmark comparison
For every selected OOS window, the walk-forward report SHALL retain and print metrics and relative total-return/CAGR differences for both fixed benchmarks. For each benchmark and difference metric, the aggregate comparison SHALL report mean, median, minimum as the worst difference, maximum, population standard deviation, total window count, valid contributing count and evidence status. It SHALL also report the total-return outperformance rate defined by this specification.

#### Scenario: Multiple OOS windows retain both comparisons
- **WHEN** a walk-forward run completes multiple OOS windows
- **THEN** each window identifies both fixed benchmarks and their comparison values
- **AND** each aggregate comparison excludes only null values for its own metric
- **AND** each benchmark retains its own magnitude summary and outperformance rate

### Requirement: Terminal report output
The system SHALL produce a terminal-readable evidence report containing per-window boundaries, generated OOS version, best parameters, train Sharpe, all five OOS metrics, skipped-combination summary, metric-local aggregate statistics and evidence status, positive-window rate, quantified IS/OOS Sharpe gaps, parameter value frequencies and transitions, and separate fixed-benchmark comparisons and win rates. The report SHALL NOT emit an automatic strategy pass/fail decision or a continuous OOS equity curve.

#### Scenario: Report includes quantified parameter stability
- **WHEN** a walk-forward run completes with 3 windows
- **THEN** the report lists each searched parameter's values by window, value frequencies, transition count, comparison count and transition rate

#### Scenario: Report remains evidence rather than decision
- **WHEN** all report statistics have been calculated
- **THEN** the terminal output presents values, counts and evidence status
- **AND** does not label the strategy as passed, failed, approved or rejected

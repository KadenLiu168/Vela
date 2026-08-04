# walk-forward-runner Specification

## Purpose
TBD - created by archiving change add-walk-forward. Update Purpose after archive.
## Requirements
### Requirement: Anchor walk-forward window splitting
The system SHALL normalize supplied historical trading dates by sorting and deduplicating those within a configured inclusive `start_date` and `end_date`, then split them into rolling training/test windows. For window index i, the calendar anchor SHALL be `start_date + i * step_years`; its training calendar interval SHALL be `[anchor, anchor + train_years)` and its test calendar interval SHALL immediately follow as `[anchor + train_years, anchor + train_years + test_years)`. Calendar-year addition SHALL day-clamp leap-day anchors. The system SHALL include only windows whose complete test calendar interval ends on or before `end_date + 1 day`, and SHALL resolve each half-open calendar interval to the first and last actual trading date before passing inclusive bounds to `run_backtest()`.

#### Scenario: Three windows from 6 calendar years
- **WHEN** the configured range is 2019-01-01 through 2024-12-31 and complete trading dates exist with train_years=3, test_years=1, step_years=1
- **THEN** the system generates exactly 3 windows with non-overlapping train/test boundaries: calendar training/testing intervals 2019-2021/2022, 2020-2022/2023, and 2021-2023/2024.

#### Scenario: Insufficient data produces no windows
- **WHEN** the configured range spans less than train_years + test_years
- **THEN** the system reports an error and executes no backtest.

#### Scenario: Partial final test window is excluded
- **WHEN** a later window's test calendar interval would end after `end_date + 1 day`
- **THEN** the system excludes that partial final window.

#### Scenario: Empty calendar interval is rejected
- **WHEN** a calendar-complete training or test interval contains no supplied trading date
- **THEN** the system reports a data error instead of emitting an invalid window.

### Requirement: Walk-forward orchestration
The system SHALL, for each window, search the parameter space on the training period, select the best parameter combination by `sharpe_ratio`, evaluate it on the test period, and aggregate results across all windows. Only successful training runs with a non-null Sharpe SHALL be eligible. Highest Sharpe SHALL win; equal values SHALL be resolved by the lexicographic order of each combination's canonical JSON representation. Every selected OOS result SHALL retain total return, annualized return, maximum drawdown, volatility and Sharpe.

#### Scenario: Single window with parameter search
- **WHEN** a walk-forward run is configured with one window and a parameter space of 2 combinations
- **THEN** the system runs exactly 2 training backtests, selects the best by Sharpe, and runs exactly 1 OOS backtest on the test window
- **AND** the window result contains the best parameters and all five OOS metrics

#### Scenario: Multiple windows aggregate OOS results
- **WHEN** a walk-forward run completes 3 windows
- **THEN** the aggregate report includes mean, median, minimum, maximum, population standard deviation, total window count and valid count for each of the five non-null OOS metrics
- **AND** labels the minimum maximum-drawdown value as the worst drawdown because maximum drawdown uses the negative-number convention

#### Scenario: Equal training Sharpe is deterministic
- **WHEN** two eligible combinations have the same highest training Sharpe
- **THEN** the system selects the combination whose canonical JSON sorts first.

### Requirement: Source writes use the caller transaction
The walk-forward runner SHALL neither commit nor roll back the caller-provided source session. The CLI SHALL execute the complete run inside the repository's managed-session boundary so all selected OOS runs and their fixed benchmark results commit only after every window succeeds and all writes from the command roll back if any later step or fixed benchmark evaluation fails.

#### Scenario: Complete run commits source outputs
- **WHEN** all windows, OOS evaluations, and fixed benchmark evaluations succeed through the CLI
- **THEN** the managed caller transaction commits all source-side outputs once.

#### Scenario: Later window failure rolls back source outputs
- **WHEN** a later OOS or fixed benchmark evaluation fails after an earlier window added source-side rows
- **THEN** the CLI exits non-zero and the managed caller transaction persists none of this command's source-side rows.

### Requirement: Persisted OOS strategy identity
Before an OOS backtest is persisted, the system SHALL replace the selected config's version with `wf-` plus the first 12 lowercase hexadecimal characters of SHA-256 over canonical JSON of the complete validated configuration excluding its original version. The report SHALL include that generated version and the complete selected parameter combination. Different effective configurations SHALL NOT reuse the same generated identity within one run.

#### Scenario: Same effective config has stable version
- **WHEN** the same effective validated strategy configuration is selected in two windows
- **THEN** both OOS runs use the same deterministic walk-forward version.

#### Scenario: Different parameters have isolated versions
- **WHEN** two windows select different effective parameter values
- **THEN** their generated config versions differ and the persisted report mapping identifies each version's complete selected parameters.

### Requirement: OOS dual-benchmark comparison
For every selected OOS window, the walk-forward report SHALL retain and print metrics and relative total-return/CAGR differences for both fixed benchmarks. For each benchmark and difference metric, the aggregate comparison SHALL report mean, median, minimum as the worst difference, maximum, population standard deviation, total window count, valid contributing count and evidence status. It SHALL also report the total-return outperformance rate defined by this specification.

#### Scenario: Multiple OOS windows retain both comparisons
- **WHEN** a walk-forward run completes multiple OOS windows
- **THEN** each window identifies both fixed benchmarks and their comparison values
- **AND** aggregate comparison values exclude only null values for their own metric

### Requirement: OOS evidence sufficiency
Every OOS metric summary and rate SHALL expose its total window count, valid contributing count, and an evidence status. Evidence status SHALL be `sufficient` only when at least three windows contribute a valid value and SHALL otherwise be `insufficient_evidence`. The status SHALL represent only this minimum-count threshold and MUST NOT imply window independence, statistical adequacy or strategy validity. Insufficient evidence MUST NOT prevent the report from being generated and MUST NOT be converted into an automatic strategy pass or failure.

#### Scenario: Two valid windows remain reportable
- **WHEN** a walk-forward run has two valid OOS total-return observations
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
The walk-forward report SHALL treat each OOS backtest as an independent evaluation interval and MUST NOT concatenate or link their equity curves, compute cross-window path metrics, or represent them as one continuously tradable portfolio.

#### Scenario: Adjacent windows do not create a continuous curve
- **WHEN** one OOS window ends immediately before the next window starts
- **THEN** the report retains both window results separately
- **AND** does not synthesize a boundary return or continuous OOS net-value series

### Requirement: Terminal report output
The system SHALL produce a terminal-readable evidence report containing per-window boundaries, generated OOS version, best parameters, train Sharpe, all five OOS metrics, skipped-combination summary, metric-local aggregate statistics and evidence status, positive-window rate, quantified IS/OOS Sharpe gaps, parameter value frequencies and transitions, and separate fixed-benchmark comparisons and win rates. The report SHALL NOT emit an automatic strategy pass/fail decision or a continuous OOS equity curve.

#### Scenario: Report includes parameter stability
- **WHEN** a walk-forward run completes with 3 windows
- **THEN** the report lists each searched parameter's values by window, value frequencies, transition count, comparison count and transition rate

#### Scenario: Report remains evidence rather than decision
- **WHEN** all report statistics have been calculated
- **THEN** the terminal output presents values, counts and evidence status
- **AND** does not label the strategy as passed, failed, approved or rejected

### Requirement: CLI command
The system SHALL provide a `vela walk-forward` CLI command that accepts a walk-forward YAML configuration path, an optional database URL using the same default as other database commands, and an optional report output path. Relative base-strategy paths in the walk-forward YAML SHALL resolve relative to that YAML file. The command SHALL execute the full analysis against SQLite only.

#### Scenario: CLI invocation
- **WHEN** the user runs `vela walk-forward --config config/walk_forward_v1.yaml`
- **THEN** the system loads the configuration, executes the walk-forward run, prints the report to stdout, and exits with code 0 on success.

#### Scenario: CLI with invalid config
- **WHEN** the user runs `vela walk-forward --config nonexistent.yaml`
- **THEN** the system exits with a non-zero code and prints an error message indicating the config file could not be found.

#### Scenario: Report output file
- **WHEN** the user supplies `--output /tmp/walk-forward-report.txt`
- **THEN** the command writes the same complete report to that path and prints a confirmation.

#### Scenario: Non-SQLite database rejected
- **WHEN** the user supplies a non-SQLite database URL
- **THEN** the command fails before any backtest with a clear SQLite-only message.
### Requirement: Selected OOS evidence includes expanded risk metrics
After `strengthen-walk-forward-evaluation-contract`, each selected OOS window SHALL retain strategy Sortino, Calmar and longest drawdown duration and each fixed benchmark comparison SHALL retain Tracking Error and Information Ratio. The report SHALL aggregate each strategy metric and each benchmark-relative metric separately using the existing metric-local valid-count and evidence-status contract.

#### Scenario: OOS windows aggregate downside metrics
- **WHEN** three selected OOS runs contain valid Sortino and Calmar values
- **THEN** the evidence report includes their descriptive summaries and sufficient valid counts

#### Scenario: Benchmark active metrics remain keyed
- **WHEN** selected OOS runs contain TE/IR for both fixed benchmarks
- **THEN** the report aggregates TE/IR separately for `equal_weight_monthly` and `csi_300_buy_hold`

#### Scenario: Expanded evidence does not join curves
- **WHEN** expanded OOS metrics are reported across adjacent windows
- **THEN** the windows remain independent
- **AND** no continuous OOS curve or cross-window Calmar/drawdown duration is calculated

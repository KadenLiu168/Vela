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
The system SHALL, for each window, search the parameter space on the training period, select the best parameter combination by `sharpe_ratio`, evaluate it on the test period, and aggregate results across all windows. Only successful training runs with a non-null Sharpe SHALL be eligible. Highest Sharpe SHALL win; equal values SHALL be resolved by the lexicographic order of each combination's canonical JSON representation.

#### Scenario: Single window with parameter search
- **WHEN** a walk-forward run is configured with one window and a parameter space of 2 combinations
- **THEN** the system runs exactly 2 training backtests (one per combination), selects the best by Sharpe, runs exactly 1 OOS backtest on the test window, and returns a result containing the best parameters and OOS metrics.

#### Scenario: Multiple windows aggregate OOS results
- **WHEN** a walk-forward run completes 3 windows
- **THEN** the aggregate report SHALL include the mean, median, minimum, maximum, and population standard deviation of non-null OOS Sharpe across all windows and SHALL identify any window with a null OOS Sharpe.

#### Scenario: Equal training Sharpe is deterministic
- **WHEN** two eligible combinations have the same highest training Sharpe
- **THEN** the system selects the combination whose canonical JSON sorts first.

### Requirement: Source writes use the caller transaction
The walk-forward runner SHALL neither commit nor roll back the caller-provided source session. The CLI SHALL execute the complete run inside the repository's managed-session boundary so all OOS and baseline writes commit only after every window succeeds and all writes from the command roll back if any later step fails.

#### Scenario: Complete run commits source outputs
- **WHEN** all windows, OOS evaluations, and enabled baseline evaluations succeed through the CLI
- **THEN** the managed caller transaction commits all source-side outputs once.

#### Scenario: Later window failure rolls back source outputs
- **WHEN** a later OOS or baseline evaluation fails after an earlier window added source-side rows
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
For every selected OOS window, the walk-forward report SHALL retain and print metrics and relative total-return/CAGR differences for both fixed benchmarks. Its aggregate comparison section SHALL report the mean and contributing-window count for each benchmark's non-null total-return and annualized-return difference.

#### Scenario: Multiple OOS windows retain both comparisons
- **WHEN** a walk-forward run completes multiple OOS windows
- **THEN** each window identifies both fixed benchmarks and their comparison values
- **AND** aggregate comparison values exclude only null values for their own metric

### Requirement: Terminal report output
The system SHALL produce a terminal-readable text report containing per-window boundaries, generated OOS version, best parameters, train Sharpe, OOS Sharpe, OOS annualized return, OOS maximum drawdown, skipped-combination summary, aggregate OOS statistics, parameter stability analysis, and fixed benchmark comparisons.

#### Scenario: Report includes parameter stability
- **WHEN** a walk-forward run completes with 3 windows
- **THEN** the report SHALL list the best parameter value for each searched parameter in each window, allowing the user to assess whether the optimal parameters are stable across windows.

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

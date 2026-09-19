# dashboard-aggregation Specification

## Purpose
Define the Dashboard first-screen aggregate read model across strategy configuration, market price coverage, latest signal, and recent backtest state.

## Requirements

### Requirement: Dashboard aggregate read model
The system SHALL provide a core dashboard aggregation service that returns first-screen strategy, market data, latest successful signal, and backtest state in one read model.

#### Scenario: Aggregate dashboard state
- **WHEN** backend code requests the dashboard aggregate with a SQLAlchemy session and current application configuration
- **THEN** the result includes strategy summary data
- **AND** the result includes market data status
- **AND** the result includes latest successful signal summary data when a successful signal exists
- **AND** the result includes recent backtest summary data when a backtest exists

#### Scenario: Empty persisted workflow data
- **WHEN** backend code requests the dashboard aggregate and the local database has no market prices, successful signals, or backtests
- **THEN** the market data status reports zero price rows and zero covered ETFs
- **AND** the latest signal summary is null
- **AND** the recent backtest summary is null

### Requirement: Dashboard market data status uses persisted market prices

The dashboard aggregation service SHALL calculate market data status from real `MarketPrice` rows stored in SQLite.

#### Scenario: Market price coverage summary

- **WHEN** persisted market price rows exist for multiple ETFs and trade dates
- **THEN** the market data status reports the total market price row count
- **AND** it reports the distinct covered ETF count
- **AND** it reports the earliest and latest persisted trade dates across all ETFs
- **AND** each ETF in the `etf_list` includes its `etf_id`
- **AND** each ETF in the `etf_list` includes its own earliest persisted trade date

### Requirement: Dashboard latest signal summary
The dashboard aggregation service SHALL summarize the latest successful persisted strategy signal
for the exact, case-sensitive current `strategy_id` and `config_version` for first-screen review.

#### Scenario: Latest successful signal exists
- **WHEN** multiple persisted strategy signals exist
- **THEN** the latest signal summary uses the successful signal with the newest generated timestamp and id tie-breaker whose `strategy_id` and `config_version` match the current strategy config
- **AND** it ignores failed, running, and partial signals
- **AND** it ignores signals belonging to other strategies or other config versions
- **AND** it includes signal id, signal date, config version, status, result, generated timestamp, fallback status, and position count

#### Scenario: Latest successful signal does not exist
- **WHEN** persisted strategy signals exist but none have success status for the current strategy id and config version
- **THEN** the latest signal summary is null

#### Scenario: Latest signal fallback status
- **WHEN** the latest successful signal for the current strategy id and config version has a persisted position without rank and score values
- **THEN** the latest signal summary marks fallback status as active

### Requirement: Dashboard recent backtest summary
The dashboard aggregation service SHALL summarize the most recent persisted backtest run **for the exact, case-sensitive current `strategy_id`** for first-screen review. It SHALL NOT summarize another strategy's run: the summary is paired with the current strategy's latest signal in one first-screen read model, so reporting a foreign strategy's run there would state that run's performance as this strategy's. Config versions SHALL NOT be filtered, because runs of the same strategy are comparable evidence and the summary reports each run's `config_version`.

#### Scenario: Recent backtest exists
- **WHEN** multiple persisted backtest runs exist
- **THEN** the recent backtest summary uses the run with the newest start timestamp and id tie-breaker
- **AND** it includes run id, strategy id, config version, date range, status, total return, max drawdown, Sharpe ratio, and start timestamp

#### Scenario: Another strategy's run is not reported
- **WHEN** the newest persisted backtest run belongs to a different strategy id than the current strategy
- **THEN** the recent backtest summary uses the newest run belonging to the current strategy id
- **AND** it is null when no run belongs to the current strategy id

#### Scenario: A stale config version is still reported as evidence
- **WHEN** the current strategy's newest run was produced under an earlier `config_version` than the current one
- **THEN** the summary reports that run
- **AND** it carries the run's own `config_version` so the version mismatch is visible

### Requirement: Dashboard recent market data fetch logs
The dashboard aggregation service SHALL include recent market data fetch log summaries from persisted `DataFetchLog` rows.

#### Scenario: Recent fetch logs exist
- **WHEN** backend code requests the dashboard aggregate and persisted `DataFetchLog` rows exist
- **THEN** the result includes recent fetch log summaries ordered newest first
- **AND** each summary includes fetch time, fetch mode, status, fetched row count, inserted row count, updated row count, and error summary

#### Scenario: No fetch logs exist
- **WHEN** backend code requests the dashboard aggregate and no `DataFetchLog` rows exist
- **THEN** the result includes an empty recent fetch log list

### Requirement: Dashboard latest signal summary carries target holdings
The dashboard aggregation service SHALL include the latest successful signal's persisted target holdings in the latest signal summary, in addition to the existing summary fields. Each holding SHALL carry the ETF's exchange, symbol, and name, the position's target weight, rank, and score, and whether that position is a fallback position. Holdings SHALL be ordered by rank with unranked positions last. A successful signal with no persisted positions SHALL produce an empty holdings collection and SHALL NOT be reported as absent. The summary SHALL also carry the signal's `source` and its `backtest_run_id`, because the latest successful signal for the current strategy and config version may be a simulation artifact produced by a backtest rather than a live generation, and a consumer cannot label that honestly without them.

#### Scenario: Signal provenance is projected
- **WHEN** the latest successful signal was produced by a backtest
- **THEN** the summary carries `source` equal to that persisted source value
- **AND** it carries the persisted `backtest_run_id`

#### Scenario: A live signal projects a null run link
- **WHEN** the latest successful signal has source `manual` or `scheduled`
- **THEN** the summary carries that source
- **AND** its `backtest_run_id` is null

#### Scenario: Holdings are projected from the persisted signal
- **WHEN** the latest successful signal for the current strategy and config version has persisted positions
- **THEN** the summary includes one entry per position carrying exchange, symbol, name, target weight, rank, score, and the position-level fallback flag
- **AND** the existing summary fields keep their current values

#### Scenario: Fallback positions are projected
- **WHEN** a persisted position has a null rank and a null score
- **THEN** its projected entry carries a null rank, a null score, and a true fallback flag

#### Scenario: No positions yields an empty collection
- **WHEN** the latest successful signal has no persisted positions
- **THEN** the summary is present with an empty holdings collection
- **AND** the existing position count is zero

#### Scenario: No successful signal keeps the summary null
- **WHEN** no successful signal exists for the current strategy and config version
- **THEN** the latest signal summary remains null

### Requirement: Dashboard recent backtest summary carries benchmark comparison
The dashboard aggregation service SHALL include the recent backtest's persisted benchmark comparison in the recent backtest summary, in addition to the existing summary fields. Each benchmark entry SHALL carry the benchmark key and display name, its total return, annualized return, Sharpe ratio, and max drawdown, and the strategy-minus-benchmark total-return and annualized-return differences. The projection SHALL NOT include benchmark net-value curves or expanded risk, regime, or distribution metrics. A run with no persisted benchmarks SHALL produce an empty collection.

#### Scenario: Benchmarks are projected for a benchmark-enabled run
- **WHEN** the most recent persisted backtest run has persisted benchmark rows
- **THEN** the summary includes one entry per benchmark carrying key, display name, the four metric values, and the two difference values
- **AND** the projection contains no benchmark curve points

#### Scenario: Legacy run yields an empty collection
- **WHEN** the most recent persisted backtest run has no persisted benchmarks
- **THEN** the summary is present with an empty benchmark collection
- **AND** no benchmark value is fabricated

### Requirement: Dashboard reports the latest walk-forward run for the current strategy
The dashboard aggregation service SHALL include the latest walk-forward run for the current strategy, ordered with non-terminal runs (`queued`, `running`) first and terminal runs by finish time, as the latest-state-wins source. The summary SHALL carry the run id, status, strategy id, test start and end dates, window count, finish timestamp, and error message. When no walk-forward run exists for the current strategy the field SHALL be null.

#### Scenario: Latest run is selected for the current strategy
- **WHEN** multiple walk-forward runs exist for the current strategy
- **THEN** the summary uses the non-terminal run when one exists, otherwise the run with the newest finish time and id tie-breaker

#### Scenario: Other strategies do not contribute
- **WHEN** walk-forward runs exist only for a different strategy id
- **THEN** the latest walk-forward field is null

#### Scenario: No run yields null
- **WHEN** no walk-forward run exists locally
- **THEN** the latest walk-forward field is null

### Requirement: Dashboard projects persisted walk-forward OOS evidence without recomputation
For a walk-forward summary whose run status is `success`, the dashboard aggregation service SHALL include a projected out-of-sample evidence object read from the run's persisted evidence document after validating that document against its declared evidence version. The projection SHALL carry the window count and, for the strategy's total return, Sharpe ratio, and max drawdown, the summary's median, mean, window count, valid count, and evidence status; the positive-window rate's value, numerator, denominator, window count, valid count, and evidence status; the generalization gap's median, mean, window count, valid count, and evidence status; and, per persisted benchmark key, that benchmark's outperformance rate summary. The projection SHALL NOT include per-window records, parameter-stability records, regime or distribution evidence, or any value recomputed from raw prices. For a run whose status is not `success` the evidence object SHALL be null, and a non-success run SHALL NOT be reported with projected evidence.

#### Scenario: Successful run projects persisted aggregates
- **WHEN** the latest walk-forward run has status `success` and a valid persisted evidence document
- **THEN** the projected evidence carries the strategy metric summaries, the positive-window rate, the generalization gap, and one outperformance rate per persisted benchmark key
- **AND** every projected number equals the persisted evidence value

#### Scenario: Non-success runs project no evidence
- **WHEN** the latest walk-forward run is `queued`, `running`, or `failed`
- **THEN** the evidence object is null
- **AND** the run's status, dates, window count, and error message remain available

#### Scenario: Projection omits deep-window records
- **WHEN** a successful run's evidence document contains per-window and parameter-stability records
- **THEN** the projected evidence does not include them

#### Scenario: The dashboard read does not recompute window ownership
- **WHEN** the dashboard aggregate is requested
- **THEN** the projection reads the run row and its evidence document only
- **AND** it does not load the run's window children or their out-of-sample backtest runs

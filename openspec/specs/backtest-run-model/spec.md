# backtest-run-model Specification

## Purpose
Define the backtest run persistence contract used by historical backtesting and later result analysis.
## Requirements
### Requirement: Backtest run ORM model
The system SHALL define a `BacktestRun` SQLAlchemy ORM model for one historical backtest execution.

#### Scenario: Model exposes backtest run fields
- **WHEN** backend code inspects the `BacktestRun` model table
- **THEN** the table includes columns for `id`, `strategy_id`, `config_version`, `start_date`, `end_date`, `parameters_json`, `data_snapshot_json`, `started_at`, `finished_at`, `status`, `error_message`, `total_return`, `annualized_return`, `max_drawdown`, `sharpe_ratio`, `volatility`, `created_at`, and `updated_at`

#### Scenario: Backtest run status values
- **WHEN** backend code creates backtest run rows for execution lifecycle states
- **THEN** the model supports `running`, `success`, `failed`, and `partial` status values

#### Scenario: Optional run completion fields
- **WHEN** backend code inspects the `BacktestRun` model table
- **THEN** `finished_at`, `error_message`, `total_return`, `annualized_return`, `max_drawdown`, `sharpe_ratio`, and `volatility` are nullable

### Requirement: Backtest run history
The system SHALL preserve multiple backtest runs for the same strategy id, configuration version, and date range.

#### Scenario: Same strategy config and date range rerun
- **WHEN** two backtest run rows use the same `strategy_id`, `config_version`, `start_date`, and `end_date` values
- **THEN** the database allows both rows

#### Scenario: Inspect backtest run indexes
- **WHEN** backend code inspects the `BacktestRun` model table indexes
- **THEN** indexes exist for querying by strategy id and configuration version, by status and start timestamp, and by requested start and end date

### Requirement: Backtest parameter snapshot
The system SHALL store the backtest parameter snapshot used for a run.

#### Scenario: Store serialized parameters
- **WHEN** backend code creates a backtest run row with serialized parameter data
- **THEN** the model can store the parameter data in `parameters_json`

### Requirement: Backtest run migration metadata
The system SHALL expose ORM metadata that includes the backtest run models to Alembic migration autogeneration.

#### Scenario: Alembic target metadata includes backtest tables
- **WHEN** Alembic loads the project model metadata
- **THEN** the metadata includes the `backtest_run` and `backtest_equity_curve` tables
- **AND** the metadata does not include the `backtest_equity_point` table

### Requirement: Backtest equity curve ORM model
The system SHALL define a `BacktestEquityCurve` SQLAlchemy ORM model for daily net value and portfolio snapshot rows produced by a backtest run.

#### Scenario: Model exposes equity curve fields
- **WHEN** backend code inspects the `BacktestEquityCurve` model table
- **THEN** the table includes columns for `id`, `backtest_run_id`, `trade_date`, `net_value`, `cash`, `market_value`, `total_assets`, `positions_json`, and `created_at`

#### Scenario: Equity curve references backtest run
- **WHEN** backend code inspects the `BacktestEquityCurve` model table
- **THEN** `backtest_run_id` references the `BacktestRun` table primary key

#### Scenario: Equity curve relationship exposes run data
- **WHEN** backend code loads a backtest run with related equity curve rows
- **THEN** the ORM exposes the curve through `BacktestRun.equity_curve` and the parent run through `BacktestEquityCurve.backtest_run`

### Requirement: Backtest equity curve identity
The system SHALL prevent duplicate equity curve rows within the same backtest run and trading date.

#### Scenario: Same run and same trading date
- **WHEN** two equity curve rows use the same `backtest_run_id` and `trade_date` values
- **THEN** the database rejects the duplicate row

#### Scenario: Same trading date in different backtest runs
- **WHEN** two equity curve rows use different `backtest_run_id` values with the same `trade_date`
- **THEN** the database allows both rows

#### Scenario: Inspect equity curve indexes
- **WHEN** backend code inspects the `BacktestEquityCurve` model table indexes
- **THEN** an index exists for querying equity curve rows by backtest run and trading date

### Requirement: Persist backtest results
The system SHALL persist a completed backtest result by creating a new `BacktestRun` row and related `BacktestEquityCurve` rows from caller-provided result data.

#### Scenario: Persist run metadata and metrics
- **WHEN** backend code persists a backtest result with strategy metadata, parameter JSON, lifecycle fields, and metric values
- **THEN** the database stores a new `BacktestRun` row with those values

#### Scenario: Persist equity curve rows
- **WHEN** backend code persists a backtest result with equity curve row inputs
- **THEN** the database stores `BacktestEquityCurve` rows linked to the newly created `BacktestRun`
- **AND** each curve row stores trade date, net value, cash, market value, total assets, and positions JSON

#### Scenario: Preserve rerun history
- **WHEN** backend code persists two backtest results for the same strategy id, configuration version, and date range
- **THEN** the database stores two separate `BacktestRun` rows

### Requirement: Query persisted backtest results
The system SHALL provide a query helper for retrieving a persisted backtest run with its equity curve rows.

#### Scenario: Load run with equity curve
- **WHEN** backend code queries a persisted backtest result by run id
- **THEN** the system returns the matching `BacktestRun`
- **AND** the run includes its related equity curve rows
- **AND** the equity curve rows are ordered by trade date and row id

#### Scenario: Missing run
- **WHEN** backend code queries a backtest run id that does not exist
- **THEN** the system returns no result

### Requirement: Export backtest report
The system SHALL export a human-readable report for a persisted backtest run selected by run id.

#### Scenario: Report core run fields
- **WHEN** backend code exports a report for an existing backtest run id
- **THEN** the report includes run id, strategy id, config version, date range, status, timestamps, and parameter JSON
- **AND** the report includes total return, annualized return, maximum drawdown, volatility, and Sharpe ratio

#### Scenario: Report equity curve summary
- **WHEN** backend code exports a report for a backtest run with equity curve rows
- **THEN** the report includes the equity curve point count
- **AND** the report includes the first and last curve rows
- **AND** the report includes the minimum and maximum net value rows

#### Scenario: Report empty equity curve
- **WHEN** backend code exports a report for a backtest run without equity curve rows
- **THEN** the report states that no equity curve rows are present

#### Scenario: Missing backtest run
- **WHEN** backend code exports a report for a run id that does not exist
- **THEN** the system raises a not-found error

### Requirement: Backtest run exposes its strategy signals

The ORM SHALL expose a bidirectional relationship between `BacktestRun` and `StrategySignal` through `StrategySignal.backtest_run_id`.

#### Scenario: Run exposes ordered signals
- **WHEN** backend code loads a backtest run with linked strategy signals
- **THEN** `BacktestRun.signals` contains only signals whose `backtest_run_id` equals that run id
- **AND** the signals are ordered by `signal_date` ascending then `id` ascending

#### Scenario: Signal exposes its run
- **WHEN** backend code loads a strategy signal with a non-null `backtest_run_id`
- **THEN** `StrategySignal.backtest_run` resolves to that run

#### Scenario: Persisted backtest query loads signals
- **WHEN** backend code calls `get_backtest_result` for an existing run
- **THEN** the returned run has both its ordered `equity_curve` and ordered `signals` collections available

### Requirement: Backtest run data snapshot
The system SHALL persist a data snapshot summary when each backtest run is created, capturing the
market-data fingerprint used by that run.

#### Scenario: Run persists data snapshot fields
- **WHEN** backend code inspects the `BacktestRun` model table after this change
- **THEN** the table includes a nullable `data_snapshot_json` column
- **AND** the column stores `min_trade_date`, `max_trade_date`, `trading_day_count`,
  `active_etf_count`, `per_etf_row_counts`, and `data_checksum`

#### Scenario: Run records snapshot on execution
- **WHEN** backend code executes a backtest run and loads its price panel
- **THEN** the run persists `data_snapshot_json` computed from the loaded panel
- **AND** the `data_checksum` is a deterministic sha256 hash over all
  `(etf_id, trade_date, close_price, factor_hfq)` rows in the panel
- **AND** the hash input orders rows by `etf_id`, then `trade_date`, and appends one UTF-8 compact
  JSON array `[etf_id, trade_date.isoformat(), str(close_price), str(factor_hfq)]` plus `"\n"`
  per row

#### Scenario: Checksum detects captured data drift
- **WHEN** two backtest runs cover the same strategy, config, and date range but a captured
  panel row's `close_price` or `factor_hfq` has changed
- **THEN** the two runs' `data_checksum` values differ
- **AND** identical captured panel rows yield identical `data_checksum` values

#### Scenario: Snapshot is optional for pre-existing rows
- **WHEN** backend code inspects a backtest run row created before this change
- **THEN** `data_snapshot_json` is nullable and may be absent without breaking queries

#### Scenario: Partial-status runs also record snapshot
- **WHEN** backend code executes a backtest run where some signals fail (resulting in `partial`
  status)
- **THEN** the run still persists `data_snapshot_json` computed from the loaded panel
- **AND** the snapshot reflects the data that was loaded for the attempt, regardless of signal
  generation outcome

#### Scenario: Snapshot covers the full loaded panel
- **WHEN** backend code computes a data snapshot from a loaded price panel
- **THEN** the loaded panel covers the selected active ETFs from the lookback buffer through the
  requested backtest `end_date`
- **AND** `min_trade_date` and `max_trade_date` reflect that full loaded-panel coverage, not just
  the rebalance dates
- **AND** `active_etf_count` counts every ETF with at least one row in the panel
- **AND** `per_etf_row_counts` maps each decimal-string ETF id to its row count within the panel
- **AND** `trading_day_count` is the count of distinct trade dates across all ETFs in the panel

#### Scenario: Snapshot does not leak future prices into signal generation
- **WHEN** the loaded panel contains dates after a historical signal's rebalance date
- **THEN** that signal receives only rows whose `trade_date` is on or before its rebalance date

#### Scenario: Empty loaded panel has a deterministic summary
- **WHEN** backend code computes a data snapshot from an empty loaded price panel
- **THEN** `min_trade_date` and `max_trade_date` are `null`
- **AND** `trading_day_count` and `active_etf_count` are `0`
- **AND** `per_etf_row_counts` is `{}`
- **AND** `data_checksum` is the sha256 digest of an empty byte stream

### Requirement: Backtest benchmark persistence model
The system SHALL persist benchmark results as child records of a `BacktestRun`. Each benchmark record SHALL store a stable benchmark key, display name, the five metric fields, and ordered daily net-value curve rows; each run SHALL contain at most one record for each benchmark key.

#### Scenario: Persist dual benchmarks with one run
- **WHEN** a benchmark-enabled run is persisted
- **THEN** it has exactly one `equal_weight_monthly` child and exactly one `csi_300_buy_hold` child
- **AND** each child has its own ordered daily net-value rows

#### Scenario: Benchmark curve identity is unique
- **WHEN** persistence attempts to add two net-value rows for the same benchmark and trade date
- **THEN** the database rejects the duplicate

### Requirement: Query benchmark results with a run
The persisted-result query helper SHALL load ordered benchmark records and their ordered curve rows with a backtest run. Runs created before benchmark support SHALL remain queryable with an empty benchmark collection.

#### Scenario: Read legacy run
- **WHEN** a caller loads a pre-benchmark backtest run
- **THEN** the run is returned without modification
- **AND** its benchmark collection is empty

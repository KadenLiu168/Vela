## ADDED Requirements

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
  JSON array `[etf_id, trade_date.isoformat(), str(close_price), str(factor_hfq)]` plus `"\\n"`
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

# backtest-execution Specification

## Purpose
Defines how a backtest is executed from local market data: trading-date resolution, historical signal generation, equity-curve and metric calculation, and normalized result persistence.
## Requirements
### Requirement: Run backtest from local market data
The system SHALL run a backtest for a strategy configuration and requested date range using local market price dates as trading dates.

#### Scenario: Resolve trading dates
- **WHEN** backend code runs a backtest with start and end dates
- **THEN** the system uses distinct `MarketPrice.trade_date` values within the inclusive date range ordered ascending

#### Scenario: Empty trading date range
- **WHEN** backend code runs a backtest for a date range with no local market prices
- **THEN** the system fails without persisting a backtest run

### Requirement: Generate signals and calculate backtest metrics
The system SHALL generate historical strategy signals before calculating the equity curve and summary metrics.

#### Scenario: Successful backtest calculation
- **WHEN** backend code runs a backtest with local trading dates and strategy configuration
- **THEN** the system generates historical strategy signals
- **AND** calculates the strategy equity curve
- **AND** calculates total return, annualized return, maximum drawdown, volatility, and Sharpe ratio

### Requirement: Persist normalized backtest results
The system SHALL persist backtest results using normalized equity curve snapshots.

#### Scenario: Persist successful run
- **WHEN** backend code completes a backtest
- **THEN** the system persists a new `BacktestRun` row with parameters, status, metrics, and timestamps
- **AND** persists `BacktestEquityCurve` rows for each equity curve point

#### Scenario: Normalized curve rows
- **WHEN** backend code maps an equity curve point with holdings to a persisted curve row
- **THEN** `total_assets` equals net value
- **AND** `market_value` equals net value
- **AND** `cash` equals `0.000000`
- **AND** `positions_json` includes the target holdings for that date

#### Scenario: Empty holdings curve row
- **WHEN** backend code maps an equity curve point without holdings to a persisted curve row
- **THEN** `total_assets` equals net value
- **AND** `market_value` equals `0.000000`
- **AND** `cash` equals net value
- **AND** `positions_json` stores an empty list

### Requirement: Trading day gap detection before backtest execution
The system SHALL detect trading-day gaps after resolving the backtest trading
dates and before generating signals, comparing the resolved trading-date union
(and each active ETF's stored dates) against the trading calendar.

By default the system MUST warn about detected gaps (printing them) and continue
the backtest. An opt-in strict mode MUST raise without persisting a backtest run
when systematic gaps exceed a configurable threshold; per-ETF gaps MUST never
trigger strict failure (they are usually suspensions, not corruption).

When the `trading_calendar` table has no rows covering the requested backtest
range, the system MUST skip gap detection with a clear warning in the default
mode, and MUST refuse to run in strict mode (a strict check has no reference to
check against).

#### Scenario: Warn about gaps by default
- **WHEN** a backtest is run with the default (non-strict) data-quality mode and the trading calendar has covering rows and systematic and/or per-ETF gaps are detected
- **THEN** the system prints the detected gaps as a warning and proceeds with the backtest

#### Scenario: No warning when dates match the calendar
- **WHEN** a backtest is run in default mode and the stored dates cover every calendar trading day in the range (per the inception-boundary rule)
- **THEN** the system prints no gap warning and proceeds with the backtest

#### Scenario: Strict mode fails on excessive systematic gaps
- **WHEN** a backtest is run in strict mode and the number of systematic gaps exceeds the configured threshold
- **THEN** the system raises without persisting a backtest run, identifying the missing trading days

#### Scenario: Strict mode tolerates gaps within threshold
- **WHEN** a backtest is run in strict mode and the number of systematic gaps is within the configured threshold
- **THEN** the system warns about the gaps and proceeds with the backtest

#### Scenario: Per-ETF gaps never trigger strict failure
- **WHEN** a backtest is run in strict mode and only per-ETF gaps are detected (no systematic gaps)
- **THEN** the system warns about the per-ETF gaps and proceeds with the backtest

#### Scenario: Skip detection when the calendar is empty in default mode
- **WHEN** a backtest is run in default mode and the `trading_calendar` table has no rows covering the requested range
- **THEN** the system prints a warning that the calendar is not synced and proceeds with the backtest without gap detection

#### Scenario: Strict mode refuses to run without a calendar
- **WHEN** a backtest is run in strict mode and the `trading_calendar` table has no rows covering the requested range
- **THEN** the system raises without persisting a backtest run, explaining that strict mode requires a synced trading calendar

### Requirement: Backtest provenance linkage is complete and atomic

`run_backtest` SHALL persist every generated historical signal with `source="backtest"`, capture every returned persisted signal id, and link exactly those signals to the newly created `backtest_run` before the caller-managed transaction commits.

#### Scenario: Completed run links every produced signal
- **WHEN** a backtest completes signal generation and result persistence
- **THEN** every persisted signal produced by that execution has `source="backtest"`
- **AND** every such signal has `backtest_run_id` equal to the new run id
- **AND** no signal outside that execution receives the new run id

#### Scenario: Missing persisted signal id aborts the run
- **WHEN** historical generation returns any result without a persisted `strategy_signal_id`
- **THEN** `run_backtest` raises before the transaction commits
- **AND** callers using the project's managed session boundary commit neither the new run nor any signals from that failed execution

#### Scenario: Link mismatch aborts the run
- **WHEN** the linkage update cannot match every distinct captured signal id as an unlinked backtest signal
- **THEN** the linkage helper raises instead of silently accepting a partial update
- **AND** callers using the project's managed session boundary roll back the signals, run, curve rows, and linkage together

#### Scenario: Concurrent or repeated runs do not cross-link signals
- **WHEN** two backtests execute for the same strategy, config version, and date range
- **THEN** each run links only the primary-key ids captured by that execution
- **AND** neither run rewrites signals already linked to another run


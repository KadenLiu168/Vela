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

### Requirement: Strategy-declared price panel lookback
The backtest SHALL resolve the selected bound strategy and size the price-panel start from its non-negative `lookback_days()` value rather than reading strategy-specific config fields. Lookback SHALL mean the number of prior trading sessions, excluding the signal session; the calendar buffer SHALL therefore provide enough observations for calculations that require the signal row plus that history.

#### Scenario: Dual-momentum lookback sizes the price panel
- **WHEN** a backtest uses dual momentum
- **THEN** lookback is the maximum short, long, and moving-average window
- **AND** the panel start uses the existing safe calendar conversion from that value
- **AND** backtest_runner does not read dual-momentum parameter fields

#### Scenario: Long-window return has signal plus prior observations
- **WHEN** dual momentum declares a long lookback of N prior sessions
- **THEN** the loaded/truncated series can include N prior observations plus the signal-date observation when local data is complete

#### Scenario: Zero-lookback strategy uses minimal buffer
- **WHEN** a strategy declares lookback 0
- **THEN** the panel start uses only the existing minimal calendar buffer
- **AND** the backtest does not require historical momentum/trend data

#### Scenario: Invalid negative lookback is rejected
- **WHEN** a registered strategy returns a negative lookback
- **THEN** backtest execution fails clearly before loading a price panel or persisting a run

### Requirement: Backtest orchestration is strategy-agnostic
Backtest execution SHALL resolve strategies through the registry, invoke generic historical signal generation, and retain the existing persistence, linkage, holdings, equity, metric, data-quality, and caller-managed transaction behavior. The persisted `parameters_json` audit payload SHALL include the selected strategy `type` in addition to the existing identity/date/risk-free-rate fields.

#### Scenario: Historical loop invokes protocol per rebalance date
- **WHEN** a backtest runs either registered strategy
- **THEN** each rebalance date is generated through the bound protocol
- **AND** no concrete strategy is imported or branched on in backtest_runner

#### Scenario: Strategy switch preserves downstream flow
- **WHEN** the same date range is run with distinct dual-momentum and equal-weight config identities
- **THEN** both runs use the same downstream persistence, linkage, holdings, equity, and metric code
- **AND** each run selects only signals from its own strategy_id and config_version

#### Scenario: Backtest audit payload records strategy type
- **WHEN** a backtest run is persisted
- **THEN** its `parameters_json` includes the selected config `type`
- **AND** no database schema change is required

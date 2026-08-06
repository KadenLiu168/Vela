# backtest-execution Specification

## Purpose
Defines how a backtest is executed from local market data: trading-date resolution, historical signal generation, equity-curve and metric calculation, and normalized result persistence.
## Requirements
### Requirement: Run backtest from local market data
The system SHALL run a backtest for a strategy configuration and requested date range using ordered official sessions from the local trading calendar as trading dates and local market prices as validated calculation inputs.

#### Scenario: Resolve trading dates
- **WHEN** backend code runs a backtest with start and end dates
- **THEN** the system uses ordered `TradingCalendar.trade_date` values within the inclusive date range
- **AND** stored `MarketPrice.trade_date` values do not define or remove curve dates

#### Scenario: Empty trading date range
- **WHEN** backend code runs a backtest for a date range with no local trading-calendar sessions
- **THEN** the system fails without generating a signal or persisting a backtest run

### Requirement: Generate signals and calculate backtest metrics
The system SHALL generate historical strategy signals before calculating the equity curve and summary metrics.

#### Scenario: Successful backtest calculation
- **WHEN** backend code runs a backtest with local trading dates and strategy configuration
- **THEN** the system generates historical strategy signals
- **AND** calculates the strategy equity curve
- **AND** calculates total return, annualized return, maximum drawdown, volatility, and Sharpe ratio

### Requirement: Persist normalized backtest results
The system SHALL persist backtest results using the actual normalized portfolio state produced by equity-curve calculation and SHALL identify the shared equity calculation semantics in run parameters.

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

#### Scenario: Persist successful drift-model run
- **WHEN** backend code completes a backtest using the continuous portfolio-state equity model
- **THEN** the system persists a new `BacktestRun` row with parameters, status, metrics, and timestamps
- **AND** `parameters_json` contains `equity_model_version` equal to `"drift_v1"`
- **AND** the system persists one `BacktestEquityCurve` row for each equity curve point

#### Scenario: Persist invested curve row
- **WHEN** backend code maps a curve point with risky-asset holdings to a persisted row
- **THEN** `total_assets` equals net value
- **AND** `cash` and `market_value` equal the curve point's calculated normalized state
- **AND** `cash + market_value` equals `total_assets`
- **AND** `positions_json` includes each ETF's `etf_id`, signal `target_weight`, and calculated `actual_weight`

#### Scenario: Persist drifted holdings
- **WHEN** a curve point's actual weights differ from its carried signal target weights
- **THEN** `positions_json` preserves both values without replacing the actual weights with target weights

#### Scenario: Persist cash-only curve row
- **WHEN** backend code maps a curve point without risky-asset holdings
- **THEN** `total_assets` equals net value
- **AND** `market_value` equals `0.000000`
- **AND** `cash` equals net value
- **AND** `positions_json` stores an empty list

#### Scenario: Runner consumes calculated state once
- **WHEN** the runner maps equity points for persistence
- **THEN** it consumes the state carried by those equity points
- **AND** it does not independently reconstruct cash, market value, or actual positions from target holding snapshots

#### Scenario: Runner rejects a point without calculated state
- **WHEN** the runner is asked to map an equity point that does not carry calculator-produced portfolio state
- **THEN** it fails explicitly instead of persisting fabricated cash, market value, or positions

#### Scenario: Historical runs remain unchanged
- **WHEN** the drift model is deployed
- **THEN** existing backtest rows are not mutated, deleted, labeled, or automatically regenerated
- **AND** runs without `equity_model_version: "drift_v1"` are not assumed to be directly comparable with drift-model runs

### Requirement: Trading day gap detection before backtest execution
The system SHALL use ordered `TradingCalendar` rows as the authoritative official-session axis for the inclusive backtest range and for the configured strategy's exact required lookback history. The system MUST validate price completeness for every ETF in the active universe passed to the configured strategy before generating or persisting any historical signal.

For each active ETF, official sessions on or after its declared `inception_date` are required; when no inception date is declared, validation begins at the exact required lookback start. Every required `(etf_id, trade_date)` MUST have a stored market-price row. Missing required calendar coverage or price rows MUST fail the backtest without any configurable warning-only mode or gap threshold.

#### Scenario: Trading calendar defines requested dates
- **WHEN** a backtest range contains official trading-calendar rows and stored market-price dates
- **THEN** the runner uses the ordered calendar rows, not the union of stored price dates, as its requested trading dates
- **AND** every resulting equity-curve interval represents consecutive official sessions

#### Scenario: Exact strategy lookback sessions are validated
- **WHEN** the configured strategy requires a positive number of lookback trading sessions
- **THEN** the runner resolves the exact preceding official sessions from the trading calendar
- **AND** it validates only that exact lookback set plus the requested backtest sessions
- **AND** an unrelated missing date outside that set does not block the backtest

#### Scenario: Missing trading calendar coverage fails
- **WHEN** the trading calendar contains no official session in the requested range or fewer preceding sessions than the exact required lookback count
- **THEN** the backtest raises an actionable error before generating or persisting any signal

#### Scenario: Systematic required-date gap fails
- **WHEN** an official required trading date has no stored price for any active-universe ETF
- **THEN** the backtest raises before generating or persisting any signal
- **AND** the error identifies the missing official date

#### Scenario: Active-universe ETF gap fails
- **WHEN** an active-universe ETF lacks a stored price on any official date required for strategy calculation or backtest valuation
- **THEN** the backtest raises before generating or persisting any signal
- **AND** the error identifies the ETF and missing date
- **AND** the system does not infer suspension, forward-fill a price, or treat the missing observation as zero return

#### Scenario: Pre-inception dates are not required
- **WHEN** an active ETF has a declared inception date within or after the candidate required-date range
- **THEN** official dates before that inception are excluded from that ETF's price-completeness requirement
- **AND** the ETF is excluded from the active universe passed to strategy calculation before inception
- **AND** the ETF joins that dated active universe on the first signal date on or after inception
- **AND** stored rows before inception are excluded from the strategy-visible price history
- **AND** every required date on or after inception remains mandatory

#### Scenario: Missing inception metadata does not hide truncated history
- **WHEN** an active ETF has no declared inception date
- **THEN** its completeness requirement begins at the exact strategy lookback start
- **AND** the first stored price date is not used to suppress earlier missing dates

#### Scenario: Failure leaves no partial backtest artifacts
- **WHEN** calendar or required-price validation fails
- **THEN** no strategy signal, backtest run, equity-curve row, or signal link from that attempted execution is persisted
- **AND** transaction ownership remains with the caller-managed session

#### Scenario: Complete input preserves execution
- **WHEN** the trading calendar and every required active-universe price are complete
- **THEN** the backtest proceeds with the existing signal generation, T+1 effectiveness, portfolio state, transaction cost, and metric contracts

#### Scenario: Obsolete tolerance controls are unavailable
- **WHEN** callers migrate to mandatory input validation
- **THEN** the public Python API no longer exposes `BacktestGapDetectionConfig` or accepts `gap_detection`
- **AND** the CLI no longer exposes strict-data-quality or systematic-gap-threshold options

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
The backtest SHALL resolve the selected bound strategy and derive its exact required history from the strategy's non-negative `lookback_days()` value rather than reading strategy-specific config fields. Lookback SHALL mean the number of prior official trading sessions, excluding the signal session. A containing date-range panel MAY be loaded for query and snapshot purposes, but dates outside the exact calendar-derived set MUST NOT expand price-completeness requirements.

#### Scenario: Dual-momentum lookback sizes the price panel
- **WHEN** a backtest uses dual momentum
- **THEN** lookback is the maximum short, long, and moving-average window
- **AND** the runner selects exactly that many preceding official sessions from `TradingCalendar`
- **AND** backtest_runner does not read dual-momentum parameter fields

#### Scenario: Long-window return has signal plus prior observations
- **WHEN** dual momentum declares a long lookback of N prior sessions
- **THEN** the loaded/truncated series can include N prior observations plus the signal-date observation when local data is complete

#### Scenario: Zero-lookback strategy requires no preceding session
- **WHEN** a strategy declares lookback 0
- **THEN** the exact required calendar set begins with the requested backtest sessions
- **AND** the backtest does not require a preceding history session

#### Scenario: Invalid negative lookback is rejected
- **WHEN** a registered strategy returns a negative lookback
- **THEN** backtest execution fails clearly before loading a price panel or persisting a run

### Requirement: Backtest orchestration is strategy-agnostic
Backtest execution SHALL resolve strategies through the registry, invoke generic historical signal generation, and retain shared persistence, linkage, holdings, equity, metric, mandatory input-validation, and caller-managed transaction behavior without branching on a concrete strategy. The persisted `parameters_json` audit payload SHALL include the selected strategy `type` in addition to the existing identity/date/risk-free-rate fields.

#### Scenario: Historical loop invokes protocol per rebalance date
- **WHEN** a backtest runs either registered strategy
- **THEN** each rebalance date is generated through the bound protocol
- **AND** each invocation receives only ETFs eligible on that date and no stored rows before their declared inception
- **AND** no concrete strategy is imported or branched on in backtest_runner

#### Scenario: Strategy switch preserves downstream flow
- **WHEN** the same date range is run with distinct dual-momentum and equal-weight config identities
- **THEN** both runs use the same downstream persistence, linkage, holdings, equity, and metric code
- **AND** each run selects only signals from its own strategy_id and config_version

#### Scenario: Backtest audit payload records strategy type
- **WHEN** a backtest run is persisted
- **THEN** its `parameters_json` includes the selected config `type`
- **AND** no database schema change is required

### Requirement: Backtest scoping of signal ids
The system SHALL pass the set of signal ids produced by a backtest run into the holdings/equity
calculation so that the run's results depend only on its own signals.

#### Scenario: Run passes its signal ids to holdings calculation
- **WHEN** backend code executes a backtest run that generated a set of signal ids
- **THEN** the holdings calculation is invoked with those `signal_ids`
- **AND** the computed holdings reflect only those signals

#### Scenario: Run passes its signal ids to equity curve calculation
- **WHEN** backend code executes a backtest run that generated a set of signal ids
- **THEN** the equity curve calculation is invoked with those `signal_ids`
- **AND** the equity curve's holding snapshots are derived from only those signals
- **AND** all derived metrics (CAGR, volatility, Sharpe, max drawdown) are computed from an equity curve that depends only on this run's signals

#### Scenario: Signal ids are extracted before holdings and equity curve computation
- **WHEN** backend code executes a backtest run
- **THEN** the `signal_ids` list is extracted from `signal_results` before `calculate_strategy_equity_curve` and `calculate_portfolio_holdings` are called
- **AND** both functions receive the same `signal_ids` list

#### Scenario: Rerun isolation
- **WHEN** the same strategy, config version, and date range is backtested a second time producing a
  new set of signal ids
- **THEN** the second run's results are independent of the first run's signals
- **AND** both runs remain separately queryable

### Requirement: Benchmark-enabled backtest orchestration
Normal `run_backtest` execution SHALL calculate the two fixed benchmarks from validated local inputs before persisting the completed run. Internal training calls used by Walk-forward parameter selection SHALL be able to skip benchmark calculation; selected OOS and normal runs SHALL not skip it.

#### Scenario: Normal run persists strategy and benchmarks together
- **WHEN** a normal backtest completes with complete local data
- **THEN** it calculates the strategy curve and both benchmark curves
- **AND** it persists their results within the caller-managed transaction

#### Scenario: Training run skips benchmark work
- **WHEN** Walk-forward evaluates a parameter combination on an IS training window
- **THEN** it evaluates the strategy Sharpe without calculating or persisting benchmark results

#### Scenario: OOS run includes benchmarks
- **WHEN** Walk-forward evaluates the selected parameter combination on an OOS window
- **THEN** it calculates and persists both fixed benchmark results for that window

### Requirement: Expanded performance metrics are calculated and persisted atomically
Benchmark-enabled execution SHALL validate benchmark identity and official-session price completeness and construct benchmark curves before strategy signal generation. After the strategy curve exists, normal success/partial and selected Walk-forward OOS backtests SHALL calculate expanded strategy metrics, benchmark metrics and aligned TE/IR before result persistence. Internal Walk-forward training trials that skip benchmarks SHALL calculate strategy-only expanded metrics inside their isolated training snapshot. `run_backtest` MUST NOT commit or roll back the caller's transaction; the caller-managed boundary SHALL commit or roll back signals, runs, curves, existing metrics, expanded metrics and metric-version snapshots together.

#### Scenario: Successful run persists one metric version
- **WHEN** a normal backtest completes successfully
- **THEN** its strategy and both benchmark records persist every calculable expanded metric atomically
- **AND** its parameter snapshot records `performance_metrics_v1`

#### Scenario: Partial run persists the calculated strategy and benchmark set
- **WHEN** a normal benchmark-enabled backtest reaches metric calculation and completes with `partial` status
- **THEN** its calculable strategy and benchmark expanded metrics persist atomically
- **AND** its parameter snapshot records `performance_metrics_v1`

#### Scenario: Training run calculates only isolated strategy metrics
- **WHEN** Walk-forward evaluates a parameter combination with benchmark calculation disabled
- **THEN** it calculates strategy Sortino, Calmar and duration and records `performance_metrics_v1` in the training snapshot
- **AND** no training run, benchmark or expanded metric is persisted to the source database

#### Scenario: Missing benchmark input still fails before signals
- **WHEN** a benchmark-enabled run lacks required benchmark identity or an official-session price
- **THEN** it fails before strategy signal generation and before any result artifact is flushed

#### Scenario: Late active-metric failure rolls back the caller transaction
- **WHEN** aligned active-risk calculation fails after strategy signals have been flushed but before result persistence
- **THEN** `run_backtest` propagates the failure without committing or rolling back independently
- **AND** the caller-managed transaction rolls back every signal, run, strategy curve, benchmark and benchmark curve from that attempt

#### Scenario: Existing metric values are preserved
- **WHEN** the runner adds the expanded calculations
- **THEN** existing total return, CAGR, maximum drawdown, volatility and Sharpe values remain unchanged

### Requirement: Benchmark-regime metrics participate in atomic execution
After strategy and fixed benchmark curves pass existing completeness checks, normal success/partial and selected Walk-forward OOS execution SHALL calculate benchmark-regime metrics before persistence. The calculation and all new fields SHALL remain inside the existing caller-owned transaction; a later calculation, validation, or persistence failure MUST roll back signals, runs, curves, benchmarks, existing metrics, and new comparison metrics together.

#### Scenario: Successful benchmark-enabled execution persists one versioned set
- **WHEN** a normal or selected OOS backtest completes benchmark-regime calculation successfully
- **THEN** it persists both benchmark comparison results atomically
- **AND** its parameter snapshot records `benchmark_regime_metrics_v1`

#### Scenario: Late regime-metric failure leaves no partial run
- **WHEN** benchmark-regime calculation or persistence fails after source-side artifacts have been added
- **THEN** the caller-managed transaction commits none of those artifacts

#### Scenario: Training execution keeps its existing scope
- **WHEN** an isolated Walk-forward training trial skips benchmark calculation
- **THEN** it does not calculate or persist CAPM or capture metrics

### Requirement: Distribution metrics participate in atomic execution
Normal success/partial and selected Walk-forward OOS execution SHALL calculate strategy and fixed-benchmark tail-distribution metrics before persistence. Isolated benchmark-skipping training trials SHALL calculate the strategy-only family for selection evidence without writing it to the source database. All source-side calculation and persistence SHALL remain inside the existing caller-owned transaction.

#### Scenario: Completed benchmark-enabled run persists one versioned family
- **WHEN** strategy and benchmark distribution calculations complete successfully
- **THEN** their metrics and counts persist atomically on the owning records
- **AND** the run snapshot records `tail_distribution_metrics_v1`

#### Scenario: Insufficient sample persists evidence counts and null metrics
- **WHEN** a completed curve has fewer than 100 effective returns
- **THEN** its owner persists actual observation/tail counts and null distribution metrics

#### Scenario: Late failure rolls back every artifact
- **WHEN** distribution calculation, validation, or persistence fails after source-side artifacts have been added
- **THEN** the caller-managed transaction commits no signal, run, curve, benchmark, existing metric, or distribution metric from the attempt

#### Scenario: Training trial remains isolated
- **WHEN** Walk-forward evaluates a benchmark-skipping training combination
- **THEN** its strategy-only distribution calculation and version remain inside the isolated snapshot
- **AND** no training metric or count is persisted to the source database


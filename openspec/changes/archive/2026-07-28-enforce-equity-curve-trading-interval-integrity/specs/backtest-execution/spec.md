## MODIFIED Requirements

### Requirement: Run backtest from local market data
The system SHALL run a backtest for a strategy configuration and requested date range using ordered official sessions from the local trading calendar as trading dates and local market prices as validated calculation inputs.

#### Scenario: Resolve trading dates
- **WHEN** backend code runs a backtest with start and end dates
- **THEN** the system uses ordered `TradingCalendar.trade_date` values within the inclusive date range
- **AND** stored `MarketPrice.trade_date` values do not define or remove curve dates

#### Scenario: Empty trading date range
- **WHEN** backend code runs a backtest for a date range with no local trading-calendar sessions
- **THEN** the system fails without generating a signal or persisting a backtest run

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

### Requirement: Strategy-declared price panel lookback
The backtest SHALL resolve the selected bound strategy and derive its exact required history from the strategy's non-negative `lookback_days()` value rather than reading strategy-specific config fields. Lookback SHALL mean the number of prior official trading sessions, excluding the signal session. A containing date-range panel MAY be loaded for query and snapshot purposes, but dates outside the exact calendar-derived set MUST NOT expand price-completeness requirements.

#### Scenario: Dual-momentum lookback resolves exact sessions
- **WHEN** a backtest uses dual momentum
- **THEN** lookback is the maximum short, long, and moving-average window
- **AND** the runner selects exactly that many preceding official sessions from `TradingCalendar`
- **AND** backtest_runner does not read dual-momentum parameter fields

#### Scenario: Long-window return has signal plus prior observations
- **WHEN** dual momentum declares a long lookback of N prior sessions
- **THEN** the loaded and dated strategy-visible series can include N prior official-session observations plus the signal-date observation when required data is complete

#### Scenario: Zero-lookback strategy requires no preceding session
- **WHEN** a strategy declares lookback 0
- **THEN** the exact required calendar set begins with the requested backtest sessions
- **AND** the backtest does not require a preceding history session

#### Scenario: Invalid negative lookback is rejected
- **WHEN** a registered strategy returns a negative lookback
- **THEN** backtest execution fails clearly before loading a price panel or persisting a signal or run

### Requirement: Backtest orchestration is strategy-agnostic
Backtest execution SHALL resolve strategies through the registry, invoke generic historical signal generation, and retain shared persistence, linkage, holdings, equity, metric, mandatory input-validation, and caller-managed transaction behavior without branching on a concrete strategy. The persisted `parameters_json` audit payload SHALL include the selected strategy `type` in addition to the existing identity/date/risk-free-rate fields.

#### Scenario: Historical loop invokes protocol per rebalance date
- **WHEN** a backtest runs either registered strategy
- **THEN** each rebalance date is generated through the bound protocol
- **AND** each invocation receives only ETFs eligible on that date and no stored rows before their declared inception
- **AND** no concrete strategy is imported or branched on in backtest_runner

#### Scenario: Strategy switch preserves downstream flow
- **WHEN** the same date range is run with distinct dual-momentum and equal-weight config identities
- **THEN** both runs use the same mandatory calendar/price validation and downstream persistence, linkage, holdings, equity, and metric code
- **AND** each run selects only signals from its own strategy_id and config_version

#### Scenario: Backtest audit payload records strategy type
- **WHEN** a backtest run is persisted
- **THEN** its `parameters_json` includes the selected config `type`
- **AND** no database schema change is required

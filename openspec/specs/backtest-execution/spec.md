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


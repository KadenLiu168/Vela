## ADDED Requirements

### Requirement: Dashboard aggregate read model
The system SHALL provide a core dashboard aggregation service that returns first-screen strategy, market data, signal, and backtest state in one read model.

#### Scenario: Aggregate dashboard state
- **WHEN** backend code requests the dashboard aggregate with a SQLAlchemy session and current application configuration
- **THEN** the result includes strategy summary data
- **AND** the result includes market data status
- **AND** the result includes latest signal summary data when a signal exists
- **AND** the result includes recent backtest summary data when a backtest exists

#### Scenario: Empty persisted workflow data
- **WHEN** backend code requests the dashboard aggregate and the local database has no market prices, signals, or backtests
- **THEN** the market data status reports zero price rows and zero covered ETFs
- **AND** the latest signal summary is null
- **AND** the recent backtest summary is null

### Requirement: Dashboard market data status uses persisted market prices
The dashboard aggregation service SHALL calculate market data status from real `MarketPrice` rows stored in SQLite.

#### Scenario: Market price coverage summary
- **WHEN** persisted market price rows exist for multiple ETFs and trade dates
- **THEN** the market data status reports the total market price row count
- **AND** it reports the distinct covered ETF count
- **AND** it reports the earliest and latest persisted trade dates

### Requirement: Dashboard latest signal summary
The dashboard aggregation service SHALL summarize the latest persisted strategy signal for first-screen review.

#### Scenario: Latest signal exists
- **WHEN** multiple persisted strategy signals exist
- **THEN** the latest signal summary uses the signal with the newest generated timestamp and id tie-breaker
- **AND** it includes signal id, signal date, config version, status, result, generated timestamp, and position count

### Requirement: Dashboard recent backtest summary
The dashboard aggregation service SHALL summarize the most recent persisted backtest run for first-screen review.

#### Scenario: Recent backtest exists
- **WHEN** multiple persisted backtest runs exist
- **THEN** the recent backtest summary uses the run with the newest start timestamp and id tie-breaker
- **AND** it includes run id, strategy name, config version, date range, status, total return, max drawdown, Sharpe ratio, and start timestamp

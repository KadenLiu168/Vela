## MODIFIED Requirements

### Requirement: Dashboard recent backtest summary
The dashboard aggregation service SHALL summarize the most recent persisted backtest run for first-screen review.

#### Scenario: Recent backtest exists
- **WHEN** multiple persisted backtest runs exist
- **THEN** the recent backtest summary uses the run with the newest start timestamp and id tie-breaker
- **AND** it includes run id, strategy id, config version, date range, status, total return, max drawdown, Sharpe ratio, and start timestamp

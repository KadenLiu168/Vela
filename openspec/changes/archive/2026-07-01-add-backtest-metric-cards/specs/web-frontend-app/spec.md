## ADDED Requirements

### Requirement: Backtest detail metric cards
The web frontend SHALL render core performance metrics on the Backtest Detail page as metric cards sourced from the `GET /api/backtests/{run_id}` response.

#### Scenario: Backtest detail shows populated metric cards
- **WHEN** the Backtest Detail API returns total return, annualized return, maximum drawdown, volatility, and Sharpe ratio values for an existing run
- **THEN** the Backtest Detail page shows a metric card for each returned metric
- **AND** total return, annualized return, maximum drawdown, and volatility are formatted as percentages
- **AND** Sharpe ratio is formatted as a decimal value

#### Scenario: Backtest detail metric cards show null state
- **WHEN** the Backtest Detail API returns null for any core metric field
- **THEN** the corresponding metric card shows `n/a`
- **AND** the page does not treat the successful API response as an error

#### Scenario: Backtest detail metric cards use real API data
- **WHEN** frontend validation renders the Backtest Detail route with a successful detail API response
- **THEN** the visible metric card values come from the response metrics object
- **AND** the page code uses the shared backtest detail API client helper instead of static metric data

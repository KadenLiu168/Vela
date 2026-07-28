## ADDED Requirements

### Requirement: Backtest metric labels disclose annualization conventions
Every Web surface that presents annualized return, volatility, or Sharpe for a backtest SHALL visibly distinguish calendar-time CAGR from 252-trading-day return statistics without changing the underlying API field names or values.

#### Scenario: Backtest Detail labels metric conventions
- **WHEN** the Backtest Detail page renders its performance metric cards
- **THEN** `annualized_return` is labeled `CAGR (calendar-time)`
- **AND** `volatility` is labeled `Annualized volatility (252D)`
- **AND** `sharpe_ratio` is labeled `Sharpe (daily returns, 252D)`

#### Scenario: Dashboard completed-run summary labels metric conventions
- **WHEN** the Dashboard renders the completed result of a backtest operation
- **THEN** `annualized_return` is labeled `CAGR (calendar-time)`
- **AND** `volatility` is labeled `Annualized volatility (252D)`
- **AND** `sharpe_ratio` is labeled `Sharpe (daily returns, 252D)`

#### Scenario: Dashboard latest-backtest summary labels Sharpe convention
- **WHEN** the Dashboard renders the latest-backtest summary
- **THEN** its `sharpe_ratio` is labeled `Sharpe (daily returns, 252D)`

#### Scenario: Values and null formatting remain unchanged
- **WHEN** the clarified labels are rendered
- **THEN** percentage, decimal, and unavailable-value formatting continue to use the existing metric values and formatters
- **AND** the frontend does not derive Sharpe from the displayed CAGR and volatility values

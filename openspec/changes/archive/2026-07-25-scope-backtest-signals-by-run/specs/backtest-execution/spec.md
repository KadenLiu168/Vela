## ADDED Requirements

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

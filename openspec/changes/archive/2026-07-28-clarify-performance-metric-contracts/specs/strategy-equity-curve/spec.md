## ADDED Requirements

### Requirement: Performance metric annualization contracts are explicit
The system SHALL preserve and distinguish calendar-time compounded annual growth from 252-trading-day arithmetic volatility and Sharpe. CAGR SHALL remain an endpoint geometric return based on elapsed calendar days; annualized volatility and Sharpe SHALL remain statistics of the effective daily return observations after the initial placeholder point. CAGR MUST NOT be used as the numerator of the daily-return Sharpe calculation.

#### Scenario: Calendar-time CAGR remains unchanged
- **WHEN** annualized return is calculated from a valid equity curve
- **THEN** CAGR equals `(ending_net_value / starting_net_value) ^ (365 / elapsed_calendar_days) - 1`
- **AND** its exponent does not depend on the number of effective return observations

#### Scenario: Trading-day volatility and Sharpe remain unchanged
- **WHEN** volatility and Sharpe are calculated from a valid equity curve
- **THEN** both calculations use only the effective daily return observations after the initial placeholder point
- **AND** volatility uses population standard deviation multiplied by `sqrt(252)`
- **AND** Sharpe uses `mean(daily_return - risk_free_rate / 252) / population_stddev(daily_return) * sqrt(252)`

#### Scenario: Valid Sharpe consistency identity
- **WHEN** focused tests calculate unquantized moments from a controlled non-constant effective daily return sequence whose net values compound those same returns
- **THEN** they derive annualized arithmetic excess return as `mean(daily_return - risk_free_rate / 252) * 252`
- **AND** they derive annualized volatility from the same observations as `population_stddev(daily_return) * sqrt(252)`
- **AND** their ratio produces the expected Sharpe value at the public six-decimal output boundary

#### Scenario: CAGR is not a Sharpe reconstruction contract
- **WHEN** a controlled non-zero-volatility equity curve has net values compounded from its effective daily returns and has both a calculable CAGR and Sharpe
- **THEN** regression tests lock the independently hand-derived values
- **AND** they demonstrate that `(CAGR - risk_free_rate) / annualized_volatility` is not required to equal Sharpe

#### Scenario: Metric compatibility is preserved
- **WHEN** this clarification is applied
- **THEN** public Python signatures, REST and CLI payload fields, database columns, and six-decimal metric values remain unchanged
- **AND** existing persisted backtest runs are not recalculated or mutated

## MODIFIED Requirements

### Requirement: Calculate Sharpe ratio from strategy metrics
The system SHALL calculate Sharpe ratio from effective equity curve daily return observations and the configured annual risk-free rate, using `mean(daily_excess_returns) / population_stddev(daily_excess_returns) × √252`.

#### Scenario: Typical positive Sharpe ratio
- **WHEN** backend code calculates Sharpe ratio for an equity curve whose effective returns have positive mean excess return and positive population standard deviation
- **THEN** the system treats only the points after the initial equity-curve point as effective return observations
- **AND** the system computes each effective daily excess return as `daily_return - risk_free_rate / 252`
- **AND** the system returns `mean(daily_excess) / population_stddev(daily_excess) × √252`
- **AND** the result is quantized to six decimal places

#### Scenario: Initial placeholder return is excluded
- **WHEN** the initial equity-curve point has its initialization placeholder return and at least two effective return observations follow it
- **THEN** the placeholder return does not contribute to the Sharpe mean or population standard deviation

#### Scenario: Negative excess return
- **WHEN** backend code calculates Sharpe ratio for an equity curve whose mean daily excess return is negative and daily excess returns have positive standard deviation
- **THEN** the system returns a negative Sharpe ratio

#### Scenario: Insufficient equity curve data
- **WHEN** backend code calculates Sharpe ratio for an equity curve with fewer than two effective daily return observations after the initial point
- **THEN** the system returns no Sharpe ratio value

#### Scenario: Zero standard deviation of daily excess returns
- **WHEN** backend code calculates Sharpe ratio for an equity curve whose daily excess returns have zero standard deviation
- **THEN** the system returns no Sharpe ratio value

#### Scenario: Backtest execution uses the corrected observations
- **WHEN** the backtest runner calculates summary metrics for an equity curve
- **THEN** it passes that equity curve and the configured annual risk-free rate to the Sharpe calculator
- **AND** it persists the resulting nullable six-decimal Sharpe value without changing the backtest result schema

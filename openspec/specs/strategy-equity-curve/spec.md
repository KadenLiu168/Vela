# strategy-equity-curve Specification

## Purpose
Defines how the daily strategy net-value equity curve is calculated from holding snapshots and market prices across trading dates.
## Requirements
### Requirement: Calculate strategy equity curve
The system SHALL calculate a daily strategy net value curve for requested trading dates using portfolio holding snapshots and market prices, and SHALL attribute each close-to-close market-return interval to the holding snapshot effective at the interval's start.

#### Scenario: Initial net value
- **WHEN** backend code calculates an equity curve for a non-empty trading-date list
- **THEN** the first curve point has net value `1.000000`

#### Scenario: One daily weighted return
- **WHEN** backend code calculates an equity curve for two trading dates with ETFs held in the first date's snapshot and those ETFs have prices on both dates
- **THEN** the second curve point net value equals the first net value multiplied by one plus the sum of each first-snapshot ETF target weight times its price return between those dates

#### Scenario: Carry holdings through interval
- **WHEN** backend code calculates an equity curve for consecutive dates whose holding snapshots carry the same successful strategy signal
- **THEN** each close-to-close daily return uses those carried-forward target holdings

#### Scenario: Interval ending at a rebalance-effective date uses prior holdings
- **WHEN** the holding snapshot for trading date T differs from the snapshot for the prior requested trading date
- **THEN** the close-to-close market return ending on T uses the prior trading date's target holdings
- **AND** the target holdings first appearing in the T snapshot do not receive market return from before T

#### Scenario: Interval after a rebalance uses new holdings
- **WHEN** the holding snapshot for trading date T contains target holdings that differ from the prior snapshot
- **THEN** the close-to-close market return from T to the following requested trading date uses the target holdings from the T snapshot

#### Scenario: Empty prior holdings keep market return neutral
- **WHEN** backend code calculates a curve point whose prior holding snapshot has no holdings
- **THEN** the close-to-close market return contribution for that point is zero

#### Scenario: Missing price return input is neutral
- **WHEN** an ETF held in the interval-start snapshot lacks either the previous or current strategy price for a daily return
- **THEN** that ETF contributes zero to the daily weighted return

#### Scenario: Empty trading-date list
- **WHEN** backend code calculates an equity curve for an empty trading-date list
- **THEN** the returned curve is empty

### Requirement: Test strategy equity curve calculation
The system SHALL include regression tests for strategy equity curve calculation covering held-position returns, initial net value, daily net values, and both sides of a rebalance-effective boundary.

#### Scenario: Verify initial and daily net values from held-position returns
- **WHEN** the strategy equity curve is calculated for multiple trading dates with held ETFs that have complete strategy prices
- **THEN** the tests verify the first curve point has net value `1.000000`
- **AND** the tests verify each following daily net value equals the prior net value multiplied by one plus the weighted interval-start held-position return
- **AND** the tests verify each following daily return value

#### Scenario: Verify the interval ending at a rebalance uses old holdings
- **WHEN** the strategy equity curve is calculated across a date where the effective holding snapshot changes and the old and new assets have materially different returns
- **THEN** the tests verify the interval ending on that date uses the old target holdings
- **AND** the tests verify the resulting daily return and net value include losses or gains from the old holdings

#### Scenario: Verify the interval after a rebalance uses new holdings
- **WHEN** the strategy equity curve includes a complete close-to-close interval after a changed holding snapshot becomes effective
- **THEN** the tests verify that following interval uses the new target holdings
- **AND** the tests verify the new holdings receive no market return from the preceding interval

### Requirement: Apply transaction costs to strategy equity curve
The system SHALL deduct transaction costs from strategy equity curve daily returns using the transaction cost rate defined by the strategy configuration and turnover at the transition from the interval-start snapshot to the interval-end snapshot.

#### Scenario: Initial entry cost
- **WHEN** backend code calculates an equity curve point whose prior snapshot is empty and whose current snapshot contains target holdings
- **THEN** the point's daily return subtracts turnover equal to the sum of current target weights multiplied by `transaction_cost_bps / 10000`
- **AND** the empty prior snapshot contributes zero market return for that interval

#### Scenario: Rebalance cost
- **WHEN** backend code calculates an equity curve point whose current target holdings differ from the prior trading date
- **THEN** the point's daily return uses the prior snapshot for market return
- **AND** the point's daily return subtracts turnover equal to the sum of absolute target weight changes multiplied by `transaction_cost_bps / 10000`

#### Scenario: Unchanged holdings
- **WHEN** consecutive holding snapshots have identical target holdings
- **THEN** the daily return has no transaction-cost deduction

#### Scenario: Zero transaction cost
- **WHEN** backend code calculates an equity curve with strategy configuration transaction cost set to zero
- **THEN** the daily return is not reduced by transaction costs

### Requirement: Calculate annualized return from strategy equity curve
The system SHALL calculate annualized return from strategy equity curve points using first net value, last net value, and elapsed calendar days.

#### Scenario: Positive elapsed curve
- **WHEN** backend code calculates annualized return for an equity curve with at least two points, a positive starting net value, and a positive calendar-day span
- **THEN** the system returns total return equal to `ending_net_value / starting_net_value - 1`
- **AND** annualized return equal to `(ending_net_value / starting_net_value) ^ (365 / elapsed_calendar_days) - 1`

#### Scenario: Flat curve
- **WHEN** backend code calculates annualized return for an equity curve whose first and last net values are equal across a positive calendar-day span
- **THEN** the system returns total return `0.000000`
- **AND** annualized return `0.000000`

#### Scenario: Not enough elapsed time
- **WHEN** backend code calculates annualized return for an equity curve with fewer than two points or without a positive calendar-day span
- **THEN** the system returns no total return or annualized return value

#### Scenario: Non-positive starting net value
- **WHEN** backend code calculates annualized return for an equity curve whose first net value is zero or negative
- **THEN** the system returns no total return or annualized return value

### Requirement: Calculate maximum drawdown from strategy equity curve
The system SHALL calculate maximum drawdown from strategy equity curve points using each point's net value and trade date.

#### Scenario: Typical drawdown curve
- **WHEN** backend code calculates maximum drawdown for an equity curve that rises to a peak and then falls to a lower trough
- **THEN** the system returns the lowest drawdown value equal to `trough_net_value / peak_net_value - 1`
- **AND** the system returns the peak and trough dates that define that maximum drawdown interval

#### Scenario: No drawdown
- **WHEN** backend code calculates maximum drawdown for an empty, flat, or all-rising equity curve
- **THEN** the system returns maximum drawdown `0.000000`
- **AND** the system returns no peak or trough date interval

### Requirement: Calculate annualized volatility from strategy equity curve
The system SHALL calculate annualized volatility from strategy equity curve daily returns using the effective return observations after the initial curve point.

#### Scenario: Typical volatile return sequence
- **WHEN** backend code calculates volatility for an equity curve with at least two effective daily return observations after the initial point
- **THEN** the system returns annualized volatility equal to the population standard deviation of those effective daily returns multiplied by the square root of 252
- **AND** the result is quantized to six decimal places

#### Scenario: Flat return sequence
- **WHEN** backend code calculates volatility for an equity curve whose effective daily return observations are all zero
- **THEN** the system returns volatility `0.000000`

#### Scenario: Not enough effective return observations
- **WHEN** backend code calculates volatility for an equity curve with fewer than two effective daily return observations after the initial point
- **THEN** the system returns no volatility value

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

### Requirement: Test maximum drawdown calculation
The system SHALL include regression tests for maximum drawdown calculation across representative strategy net value curves.

#### Scenario: Rising curve has no drawdown
- **WHEN** backend tests calculate maximum drawdown for an all-rising strategy equity curve
- **THEN** the tests verify maximum drawdown is `0.000000`
- **AND** the tests verify no peak or trough date interval is returned

#### Scenario: Falling curve records peak-to-trough loss
- **WHEN** backend tests calculate maximum drawdown for a strategy equity curve that falls from its initial peak
- **THEN** the tests verify the maximum drawdown value equals `trough_net_value / peak_net_value - 1`
- **AND** the tests verify the peak date is the initial peak date
- **AND** the tests verify the trough date is the lowest net value date

#### Scenario: Recovery after drawdown preserves deepest interval
- **WHEN** backend tests calculate maximum drawdown for a strategy equity curve that falls and later recovers without exceeding the prior peak
- **THEN** the tests verify the maximum drawdown remains the deepest peak-to-trough loss
- **AND** the tests verify the recovery point does not replace the trough date

### Requirement: Test transaction cost calculation
The system SHALL include regression tests for strategy equity curve transaction cost calculation across turnover amounts, configured cost rates, and net value impact.

#### Scenario: Different turnover amounts
- **WHEN** backend tests calculate strategy equity curves for rebalances with different absolute target weight changes
- **THEN** the tests verify each daily return subtracts `turnover * transaction_cost_bps / 10000`

#### Scenario: Different transaction cost rates
- **WHEN** backend tests calculate strategy equity curves for the same turnover with different configured transaction cost basis points
- **THEN** the tests verify the higher cost rate produces the larger daily return deduction

#### Scenario: Net value impact
- **WHEN** backend tests calculate a strategy equity curve with transaction costs and non-zero market returns
- **THEN** the tests verify each affected net value compounds the return after transaction cost deduction

# strategy-equity-curve Specification

## Purpose
TBD - created by archiving change calculate-strategy-equity-curve. Update Purpose after archive.
## Requirements
### Requirement: Calculate strategy equity curve
The system SHALL calculate a daily strategy net value curve for requested trading dates using portfolio holding snapshots and market prices.

#### Scenario: Initial net value
- **WHEN** backend code calculates an equity curve for a non-empty trading-date list
- **THEN** the first curve point has net value `1.000000`

#### Scenario: One daily weighted return
- **WHEN** backend code calculates an equity curve for two trading dates with held ETFs that have prices on both dates
- **THEN** the second curve point net value equals the first net value multiplied by one plus the sum of each held ETF target weight times its price return between those dates

#### Scenario: Carry holdings through interval
- **WHEN** backend code calculates an equity curve for dates after a successful strategy signal and before the next successful strategy signal
- **THEN** each daily return uses the latest carried-forward target holdings for that configuration version

#### Scenario: Rebalance date uses new holdings
- **WHEN** backend code calculates an equity curve for a date with a newer successful strategy signal
- **THEN** that date's daily return uses the newer signal's target holdings

#### Scenario: Empty holdings keep net value unchanged
- **WHEN** backend code calculates an equity curve for a date whose holding snapshot has no holdings
- **THEN** that date's net value equals the prior curve point net value

#### Scenario: Missing price return input is neutral
- **WHEN** a held ETF lacks either the previous or current strategy price for a daily return
- **THEN** that ETF contributes zero to the daily weighted return

#### Scenario: Empty trading-date list
- **WHEN** backend code calculates an equity curve for an empty trading-date list
- **THEN** the returned curve is empty

### Requirement: Apply transaction costs to strategy equity curve
The system SHALL deduct transaction costs from strategy equity curve daily returns using the transaction cost rate defined by the strategy configuration.

#### Scenario: Initial entry cost
- **WHEN** backend code calculates an equity curve for a date after the initial curve point where holdings enter from an empty prior snapshot
- **THEN** the daily return subtracts turnover equal to the sum of current target weights multiplied by `transaction_cost_bps / 10000`

#### Scenario: Rebalance cost
- **WHEN** backend code calculates an equity curve for a date whose target holdings differ from the prior trading date
- **THEN** the daily return subtracts turnover equal to the sum of absolute target weight changes multiplied by `transaction_cost_bps / 10000`

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

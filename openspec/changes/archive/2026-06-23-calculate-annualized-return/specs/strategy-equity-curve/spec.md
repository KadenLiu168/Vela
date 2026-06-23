## ADDED Requirements

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

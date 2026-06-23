## ADDED Requirements

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

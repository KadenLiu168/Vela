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


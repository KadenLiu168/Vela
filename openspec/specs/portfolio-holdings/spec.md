# portfolio-holdings Specification

## Purpose
Defines how portfolio target holdings are calculated from persisted strategy signal positions across trading dates, carrying positions forward between signals.
## Requirements
### Requirement: Calculate portfolio holdings from strategy signals
The system SHALL calculate portfolio target holdings for requested trading dates using successful persisted strategy signal positions for the requested configuration version.

#### Scenario: Calculate daily holdings from a signal
- **WHEN** backend code calculates holdings for a trading date that has a successful strategy signal with target positions
- **THEN** the returned holding snapshot for that date includes each signal position ETF
- **AND** each holding uses the signal position target weight

#### Scenario: Calculate interval holdings by carrying positions forward
- **WHEN** backend code calculates holdings for an ordered interval of trading dates with successful strategy signals on some dates
- **THEN** the returned snapshots cover every requested trading date
- **AND** dates after a signal date use that latest signal's target holdings until another successful signal date is reached

#### Scenario: Empty holdings before first signal
- **WHEN** backend code calculates holdings for dates earlier than the first successful strategy signal in the requested range
- **THEN** those dates have empty holdings

#### Scenario: Carry prior signal into requested interval
- **WHEN** backend code calculates holdings for a requested trading-date interval that starts after an earlier successful strategy signal
- **THEN** the first requested date uses the earlier signal's target holdings

#### Scenario: Rebalance date changes holdings explicitly
- **WHEN** backend code calculates holdings for dates before, on, and after a later successful strategy signal
- **THEN** the date before the later signal keeps the previous holdings
- **AND** the later signal date and following dates use the later signal's target holdings

#### Scenario: Latest successful signal run wins
- **WHEN** multiple successful strategy signal runs exist for the same signal date and configuration version
- **THEN** holding calculation uses the newest generated successful signal run for that date

#### Scenario: Ignore failed signals
- **WHEN** a failed strategy signal exists on a requested trading date
- **THEN** holding calculation does not use that failed signal to change holdings


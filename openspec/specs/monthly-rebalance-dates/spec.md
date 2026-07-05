# monthly-rebalance-dates Specification

## Purpose
TBD - created by archiving change add-monthly-rebalance. Update Purpose after archive.
## Requirements
### Requirement: Monthly rebalance date generation
The system SHALL generate monthly rebalance dates from a provided trading-date sequence.

#### Scenario: Generate last available trading date per calendar month
- **WHEN** backend code generates monthly rebalance dates from trading dates spanning multiple calendar months
- **THEN** the result contains the last available input trading date for each calendar month
- **AND** each calendar month contributes at most one rebalance date
- **AND** the result is sorted by date ascending

#### Scenario: Preserve holiday and missing-date behavior
- **WHEN** a calendar month is missing one or more normal trading days because of holidays or incomplete input data
- **THEN** the result uses the last available date present in the input sequence for that calendar month
- **AND** the system does not fill missing dates
- **AND** the system does not infer natural calendar dates that are absent from the input sequence

#### Scenario: Group months across calendar year boundary
- **WHEN** the input trading dates span December of one year and January of the next
- **THEN** the system treats them as separate calendar months
- **AND** each contributes its own last available trading date

#### Scenario: Deduplicate repeated trading dates
- **WHEN** the input trading-date sequence contains duplicate dates
- **THEN** the result contains each generated rebalance date at most once

#### Scenario: Sort input trading dates
- **WHEN** the input trading dates are provided in any order
- **THEN** the result is sorted by date ascending

#### Scenario: Empty trading-date sequence
- **WHEN** backend code generates monthly rebalance dates from an empty trading-date sequence
- **THEN** the result is an empty list


## ADDED Requirements

### Requirement: Weekly rebalance date generation
The system SHALL generate weekly rebalance dates from a provided trading-date sequence.

#### Scenario: Generate last available trading date per ISO week
- **WHEN** backend code generates weekly rebalance dates from trading dates spanning multiple ISO weeks
- **THEN** the result contains the last available input trading date for each ISO week
- **AND** each ISO week contributes at most one rebalance date
- **AND** the result is sorted by date ascending

#### Scenario: Preserve holiday and missing-date behavior
- **WHEN** an ISO week is missing one or more normal trading days because of holidays or incomplete input data
- **THEN** the result uses the last available date present in the input sequence for that ISO week
- **AND** the system does not fill missing dates
- **AND** the system does not infer natural calendar dates that are absent from the input sequence

#### Scenario: Deduplicate repeated trading dates
- **WHEN** the input trading-date sequence contains duplicate dates
- **THEN** the result contains each generated rebalance date at most once

#### Scenario: Empty trading-date sequence
- **WHEN** backend code generates weekly rebalance dates from an empty trading-date sequence
- **THEN** the result is an empty list

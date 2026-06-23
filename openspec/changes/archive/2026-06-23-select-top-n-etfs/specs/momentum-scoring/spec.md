## ADDED Requirements

### Requirement: Top N ETF selection
The system SHALL select the configured Top N ETFs from ranked momentum results and return selection entries containing ETF id, rank, score, and target weight.

#### Scenario: Select configured Top N ranked ETFs
- **WHEN** backend code selects Top N ETFs from ranked momentum results using strategy configuration
- **THEN** the selected results include only the highest-ranked ETFs up to `selection.top_n`
- **AND** each selected result includes the ETF id, rank, score, and target weight

#### Scenario: Assign equal target weights to selected ETFs
- **WHEN** backend code selects one or more Top N ETFs
- **THEN** each selected result has a target weight equal to one divided by the number of selected ETFs

#### Scenario: Return all available ETFs when Top N is insufficient
- **WHEN** backend code selects Top N ETFs and fewer ranked ETFs are available than `selection.top_n`
- **THEN** the selected results include all available ranked ETFs
- **AND** target weights are assigned across the available selected ETFs

#### Scenario: Return an empty selection when no ranked ETFs exist
- **WHEN** backend code selects Top N ETFs from an empty ranked result set
- **THEN** the selected results are empty

## MODIFIED Requirements

### Requirement: Defensive asset fallback selection
The system SHALL apply the configured defensive asset when ranked ETF candidates cannot satisfy the configured Top N selection.

#### Scenario: Fallback when ranked ETFs are insufficient
- **WHEN** backend code applies defensive fallback selection and the number of ranked ETF candidates is less than `selection.top_n`
- **THEN** the selected result contains the configured `defense.asset` exchange and symbol
- **AND** the selected result has full target weight
- **AND** no risky ranked ETF candidates are selected

#### Scenario: Fallback when no ranked ETFs are available
- **WHEN** backend code applies defensive fallback selection and no ranked ETF candidates are available
- **THEN** the selected result contains the configured `defense.asset` exchange and symbol
- **AND** the selected result has full target weight
- **AND** no risky ranked ETF candidates are selected

#### Scenario: Do not fallback when Top N is satisfied
- **WHEN** backend code applies defensive fallback selection and the number of ranked ETF candidates is greater than or equal to `selection.top_n`
- **THEN** the selected results contain the configured Top N ranked ETF candidates
- **AND** the configured defensive asset is not selected

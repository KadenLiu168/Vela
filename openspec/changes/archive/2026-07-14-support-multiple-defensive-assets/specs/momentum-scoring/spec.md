## MODIFIED Requirements

### Requirement: Defensive asset fallback selection
The system SHALL apply the configured defensive assets when ranked ETF candidates cannot satisfy the configured Top N selection, allocating the full target weight equally across all configured defensive assets.

#### Scenario: Fallback when ranked ETFs are insufficient
- **WHEN** backend code applies defensive fallback selection and the number of ranked ETF candidates is less than `selection.top_n`
- **THEN** the selected results contain one entry per configured `defense.assets` entry, each with its exchange and symbol
- **AND** each selected defensive entry has an equal target weight of `1 / N` where `N` is the number of configured defensive assets
- **AND** the sum of the defensive target weights equals `1.0` within Decimal rounding tolerance (each weight is `Decimal("1") / Decimal(N)`; the total is approximately, not exactly, `1.0` for N > 1)
- **AND** no risky ranked ETF candidates are selected

#### Scenario: Single defensive asset keeps full weight
- **WHEN** backend code applies defensive fallback selection and exactly one defensive asset is configured
- **THEN** the selected result contains that single `defense.assets` entry
- **AND** the selected result has full target weight `1.0`

#### Scenario: Fallback when no ranked ETFs are available
- **WHEN** backend code applies defensive fallback selection and no ranked ETF candidates are available
- **THEN** the selected results contain one entry per configured `defense.assets` entry, each with its exchange and symbol
- **AND** each selected defensive entry has an equal target weight of `1 / N` where `N` is the number of configured defensive assets
- **AND** the sum of the defensive target weights equals `1.0` within Decimal rounding tolerance (each weight is `Decimal("1") / Decimal(N)`; the total is approximately, not exactly, `1.0` for N > 1)
- **AND** no risky ranked ETF candidates are selected

#### Scenario: Do not fallback when Top N is satisfied
- **WHEN** backend code applies defensive fallback selection and the number of ranked ETF candidates is greater than or equal to `selection.top_n`
- **THEN** the selected results contain the configured Top N ranked ETF candidates
- **AND** no defensive asset is selected

## ADDED Requirements

### Requirement: Signal detail target holdings shows ETF name
The web frontend SHALL render a target holdings table on the Signal Detail page from the by-id signal detail API `positions`, and the table SHALL include an ETF name column populated from each position's `name` field, in addition to the existing exchange, symbol, target weight, rank, score, and fallback columns.

#### Scenario: Signal Detail renders a target holdings table from the by-id API
- **WHEN** the Signal Detail page loads the signal detail for the current route id
- **THEN** the page renders a target holdings table populated from the by-id signal detail API `positions`

#### Scenario: Target holdings table includes a name column
- **WHEN** the Signal Detail page renders the target holdings table
- **THEN** the table includes a "Name" column
- **AND** the Name column is placed immediately after the Symbol column
- **AND** the existing Exchange, Target weight, Rank, Score, and Fallback columns keep their current content and relative ordering, shifting right only to accommodate the new Name column

#### Scenario: Name column is populated from the API name field
- **WHEN** a position in the signal detail API response includes a `name` value
- **THEN** the Name column shows that value for the matching row

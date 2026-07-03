## ADDED Requirements

### Requirement: Signal Detail editorial metadata and holdings table styling
The web frontend SHALL render the Signal Detail metadata and Target holdings table using the flat editorial data product visual language defined by `DESIGN.md` while preserving existing Signal Detail behavior.

#### Scenario: Signal metadata uses editorial token hierarchy
- **WHEN** the Signal Detail page renders latest signal metadata
- **THEN** the metadata block uses existing tokenized neutral surfaces, borders, spacing, and typography
- **AND** metadata labels use Slate
- **AND** metadata values use Graphite or Steel for readable data hierarchy

#### Scenario: Target holdings table uses restrained editorial styling
- **WHEN** the Signal Detail page renders target holdings
- **THEN** the table container, header, row dividers, and cells use existing Graphite, Steel, Slate, Mist, Fog, Ash, Canvas, spacing, typography, and radius tokens
- **AND** target weight, rank, and score columns are visually readable as numeric data
- **AND** the table does not introduce default blue admin-dashboard styling, box shadows, sorting, filtering, or pagination

#### Scenario: Target holdings horizontal scrolling remains available
- **WHEN** the Signal Detail page is viewed on a narrow viewport
- **THEN** the Target holdings table remains horizontally scrollable when needed
- **AND** existing Signal Detail API calls, route structure, signal API helper usage, and positions rendering data remain unchanged

#### Scenario: Signal Detail empty states remain visually consistent
- **WHEN** the Signal Detail page renders either the no-signal state or the no-target-holdings state
- **THEN** the empty state uses the shared tokenized editorial empty-state styling
- **AND** it does not treat successful empty API responses as request failures

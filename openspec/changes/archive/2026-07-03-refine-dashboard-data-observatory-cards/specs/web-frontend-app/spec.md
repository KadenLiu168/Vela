## ADDED Requirements

### Requirement: Dashboard data observatory card styling
The web frontend SHALL render the Dashboard overview cards and workflow grid using the flat editorial data observatory visual language defined by `DESIGN.md`.

#### Scenario: Dashboard cards use editorial surfaces
- **WHEN** the Dashboard route renders its overview grid
- **THEN** the grid and panels use the existing Ash, Fog, Canvas, and Mist surface tokens for backgrounds and borders
- **AND** the cards do not use box shadows or blue admin-dashboard surfaces

#### Scenario: Dashboard data hierarchy uses design text colors
- **WHEN** the Dashboard route renders panel headings, metrics, compact details, and empty states
- **THEN** headings and primary values use Graphite
- **AND** body/data text uses Steel
- **AND** metadata labels use Slate

#### Scenario: Dashboard responsive readability is preserved
- **WHEN** the Dashboard route is viewed at desktop and mobile widths
- **THEN** the overview grid remains readable without changing the Dashboard information architecture, DOM semantics, API usage, routes, data loading, or operation behavior

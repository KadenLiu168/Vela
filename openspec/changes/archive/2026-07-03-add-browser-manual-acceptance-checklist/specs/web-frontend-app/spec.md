## ADDED Requirements

### Requirement: Browser manual acceptance checklist
The web frontend SHALL provide a browser manual acceptance checklist for local validation and regression of the Phase 1 frontend workflow.

#### Scenario: Checklist covers primary workflow areas
- **WHEN** a developer opens the browser manual acceptance checklist
- **THEN** it covers Dashboard, market data fetch, signal generation, backtest execution, Signal Detail, and Backtest Detail validation areas

#### Scenario: Checklist covers key UI states
- **WHEN** a developer follows the browser manual acceptance checklist
- **THEN** it includes empty-state, error-state, and success-state checks for the relevant frontend workflow areas

#### Scenario: Checklist identifies backend data requirements
- **WHEN** a checklist step requires a running local API service, seeded SQLite data, or workflow-generated backend records
- **THEN** the checklist explicitly marks that backend data requirement

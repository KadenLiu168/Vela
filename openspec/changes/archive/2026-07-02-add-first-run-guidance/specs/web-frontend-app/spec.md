## ADDED Requirements

### Requirement: Dashboard first-run guidance
The web frontend SHALL render lightweight, non-blocking first-run guidance on the Dashboard when local setup data is missing or unavailable.

#### Scenario: Dashboard guides empty local market data setup
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has zero price rows
- **THEN** the Dashboard shows a first-run guidance surface that identifies fetching local market data as the next setup step
- **AND** existing Dashboard operation buttons remain available for direct use
- **AND** the guidance does not mention login, accounts, users, teams, hosting, deployment, production, or remote setup

#### Scenario: Dashboard guides local database initialization after load failure
- **WHEN** the Dashboard route cannot load the dashboard aggregate response
- **THEN** the Dashboard keeps the local workflow layout visible
- **AND** it shows first-run guidance that identifies initializing the local database before fetching market data as the next setup step
- **AND** existing Dashboard operation buttons remain visible for direct use
- **AND** the guidance does not mention login, accounts, users, teams, hosting, deployment, production, or remote setup

#### Scenario: Dashboard hides first-run guidance after setup data exists
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has one or more price rows
- **THEN** the Dashboard does not show the first-run guidance surface
- **AND** the regular workflow panels and operation controls remain visible

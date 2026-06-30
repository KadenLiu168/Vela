## ADDED Requirements

### Requirement: Dashboard aggregate page layout
The web frontend SHALL render the default Dashboard route as a local research workflow dashboard backed by the `GET /api/dashboard` aggregate contract.

#### Scenario: Dashboard aggregate sections render
- **WHEN** the Dashboard route receives a successful dashboard aggregate response
- **THEN** the first screen includes market data status, strategy summary, latest signal, recent backtest, and operation sections
- **AND** the sections use data from the dashboard aggregate response

#### Scenario: Dashboard supports empty workflow data
- **WHEN** the dashboard aggregate response has no latest signal or recent backtest
- **THEN** the Dashboard route renders explicit empty states for those sections without treating the response as a failure

#### Scenario: Dashboard API failure is visible
- **WHEN** the Dashboard route cannot load the dashboard aggregate response
- **THEN** the Dashboard route keeps the local workflow layout visible and shows a concise API failure state

### Requirement: Dashboard uses shared frontend API client
The web frontend SHALL call the dashboard aggregate endpoint through the shared API client module.

#### Scenario: Dashboard request uses shared endpoint helper
- **WHEN** the Dashboard route loads aggregate data
- **THEN** frontend page code uses a dashboard helper from `apps/web/src/api/client.ts` instead of calling `fetch` directly

## ADDED Requirements

### Requirement: Dashboard generate signal action
The web frontend SHALL let users trigger latest strategy signal generation from the Dashboard through the shared frontend API client.

#### Scenario: User starts signal generation
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the generate signal action
- **THEN** the frontend sends `POST /api/strategy-signals/generate` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate signal-generation submissions while the request is pending

#### Scenario: Dashboard refreshes after successful signal generation
- **WHEN** the generate signal request succeeds
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed latest signal summary is rendered from the latest Dashboard response

#### Scenario: Signal generation failure remains local to the operation
- **WHEN** the generate signal request fails
- **THEN** the Dashboard keeps the local workflow layout visible
- **AND** it shows a concise signal generation failure state
- **AND** it does not reload Dashboard aggregate data for the failed generation request

#### Scenario: Signal generation validation uses local API and SQLite
- **WHEN** frontend validation runs against a local FastAPI service configured with SQLite and sufficient market data
- **THEN** the validation can trigger `POST /api/strategy-signals/generate` through the shared frontend API client
- **AND** the backend persists the expected `StrategySignal` and `StrategySignalPosition` rows through the existing generation workflow
- **AND** the validation does not rely only on frontend mock data

## ADDED Requirements

### Requirement: Dashboard refresh and empty state refinement
The web frontend SHALL let users manually refresh Dashboard status, SHALL preserve successful operation feedback when a follow-up Dashboard refresh fails, and SHALL align Dashboard empty-state copy with the next local Dashboard action.

#### Scenario: User manually refreshes Dashboard status
- **WHEN** the Dashboard route has rendered
- **AND** the user triggers the manual Dashboard refresh action
- **THEN** the frontend reloads Dashboard status from `GET /api/dashboard` through the shared frontend API client
- **AND** the refreshed Dashboard values are rendered from the latest Dashboard response

#### Scenario: Operation success remains visible when Dashboard refresh fails
- **WHEN** a Dashboard market data fetch, signal generation, or backtest run request succeeds
- **AND** the follow-up Dashboard status refresh fails with an HTTP or network error
- **THEN** the Operations panel keeps the successful operation summary visible
- **AND** the Dashboard shows the refresh failure as a Dashboard status problem instead of replacing the operation summary with an operation failure

#### Scenario: Empty states point to matching Dashboard actions
- **WHEN** the Dashboard route receives a successful dashboard aggregate response with missing local market data, latest signal data, or recent backtest data
- **THEN** each empty state identifies the matching local Dashboard action or Operations panel control needed next
- **AND** the rendered copy does not rely on login, multi-user, remote deployment, hosting, or production assumptions

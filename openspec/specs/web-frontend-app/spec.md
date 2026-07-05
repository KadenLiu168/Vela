# web-frontend-app Specification

## Purpose
TBD - created by archiving change 2026-07-05-add-setup-bootstrap-endpoint. Update Purpose after archive.
## Requirements
### Requirement: Dashboard setup bootstrap action
The web frontend SHALL expose a Dashboard action that triggers the local setup bootstrap endpoint through the shared frontend API client and renders a three-step status display.

#### Scenario: User triggers bootstrap from the Dashboard
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the "Bootstrap / Setup database & data" action
- **THEN** the frontend sends `POST /api/setup/bootstrap` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate submissions while the request is pending

#### Scenario: Dashboard shows three-step status during and after bootstrap
- **WHEN** the bootstrap request returns a response
- **THEN** the Dashboard renders one status row per bootstrap step (`migrate`, `sync_etf_pool`, `fetch_full_market_data`) using the response's `steps` array
- **AND** each status row shows a success or failure indicator matching the step's `status`
- **AND** a failed step row shows the step's `error_message`
- **AND** the Dashboard shows the response's `total_duration_seconds` as a final total once all steps have settled

#### Scenario: Dashboard refreshes aggregate data after successful bootstrap
- **WHEN** the bootstrap request returns a response with `status = "success"`
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed market data status, latest signal status, and recent backtest status are rendered from the latest Dashboard response

### Requirement: Bootstrap button uses primary visual variant
The web frontend SHALL render the "Bootstrap / Setup database & data" Dashboard action in the primary (filled) button variant and SHALL place it at the right end of the Dashboard action list.

#### Scenario: Bootstrap button visual treatment
- **WHEN** the Dashboard renders its action list
- **THEN** the bootstrap action uses the primary (filled) button variant
- **AND** the bootstrap action is the rightmost button in the action list
- **AND** the existing "Fetch market data", "Full fetch", and "Generate signal" buttons continue to use the secondary (outline) variant


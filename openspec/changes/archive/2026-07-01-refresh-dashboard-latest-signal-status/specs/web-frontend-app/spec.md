## ADDED Requirements

### Requirement: Dashboard latest signal backfill
The web frontend SHALL backfill the Dashboard latest signal summary from persisted latest signal data after a successful Dashboard signal-generation request.

#### Scenario: Dashboard refreshes aggregate and latest signal data after generation
- **WHEN** the Dashboard generate signal request succeeds
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** it loads latest signal data from `GET /api/strategy-signals/latest`
- **AND** it renders the latest signal summary from the refreshed persisted signal state

#### Scenario: Dashboard and Signal Detail show the same persisted latest signal
- **WHEN** signal generation succeeds and the latest signal endpoint returns the generated persisted signal
- **THEN** the Dashboard latest signal summary shows the same signal id, signal date, result, fallback status, and target holding count as the Signal Detail page can read from `GET /api/strategy-signals/latest`

#### Scenario: Dashboard can restore latest signal status after browser refresh
- **WHEN** the browser refreshes after a signal has been generated and persisted
- **THEN** the Dashboard loads backend data and renders the latest persisted signal summary without relying on in-memory generation result state

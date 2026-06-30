## ADDED Requirements

### Requirement: Dashboard latest signal summary states
The web frontend SHALL render the Dashboard latest signal panel from the dashboard aggregate response with populated and empty states.

#### Scenario: Dashboard shows latest successful signal summary
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is present
- **THEN** the signal panel shows the signal date
- **AND** it shows the signal result
- **AND** it shows the fallback status
- **AND** it shows the target holding count

#### Scenario: Dashboard shows empty latest signal state
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is null
- **THEN** the signal panel shows a clear empty state indicating that no successful signal has been generated yet
- **AND** it shows a generate-signal entry point
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard latest signal summary is backed by real API data
- **WHEN** dashboard validation exercises `GET /api/dashboard` against a local SQLite database with persisted strategy signal rows
- **THEN** the returned latest signal summary provides signal date, result, fallback status, and position count values that the Dashboard page renders
- **AND** the validation does not rely only on frontend mock data

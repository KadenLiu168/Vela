## ADDED Requirements

### Requirement: Dashboard market data status states
The web frontend SHALL render the Dashboard market data status from the dashboard aggregate response with explicit populated and empty states.

#### Scenario: Dashboard shows populated market data status
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has one or more price rows
- **THEN** the market data panel shows the total price record count
- **AND** it shows the covered ETF count
- **AND** it shows the earliest trade date
- **AND** it shows the latest trade date

#### Scenario: Dashboard shows empty market data status
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose market data status has zero price rows
- **THEN** the market data panel shows a clear empty state indicating that no local market data has been stored yet
- **AND** it still shows zero price records and zero covered ETFs
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard market data status is backed by real aggregate API data
- **WHEN** dashboard validation exercises `GET /api/dashboard` against a local SQLite database with persisted market price rows
- **THEN** the returned market data status provides the same record count, ETF coverage, earliest trade date, and latest trade date that the Dashboard page renders
- **AND** the validation does not rely only on frontend mock data

## ADDED Requirements

### Requirement: API dashboard returns recent fetch logs
The API service SHALL return recent market data fetch log summaries from the dashboard aggregate response.

#### Scenario: Dashboard endpoint includes recent fetch logs
- **WHEN** an API integration test configures the app with a temporary SQLite database containing `DataFetchLog` rows
- **THEN** `GET /api/dashboard` returns recent fetch log summaries derived from those persisted rows
- **AND** the validation does not rely only on mocked dashboard data

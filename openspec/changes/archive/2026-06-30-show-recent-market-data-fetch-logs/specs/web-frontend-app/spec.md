## ADDED Requirements

### Requirement: Dashboard recent market data fetch log display
The web frontend SHALL render recent market data fetch log summaries from the dashboard aggregate response.

#### Scenario: Dashboard shows recent fetch log details
- **WHEN** the Dashboard route receives a successful dashboard aggregate response containing recent fetch log summaries
- **THEN** the Dashboard shows recent fetch time, mode, status, fetched row count, inserted row count, updated row count, and error summary for those records

#### Scenario: Dashboard shows empty fetch log history
- **WHEN** the Dashboard route receives a successful dashboard aggregate response with no recent fetch logs
- **THEN** the Dashboard shows a concise empty state for fetch history
- **AND** it does not treat the successful dashboard aggregate response as an API failure

## ADDED Requirements

### Requirement: Dashboard recent market data fetch logs
The dashboard aggregation service SHALL include recent market data fetch log summaries from persisted `DataFetchLog` rows.

#### Scenario: Recent fetch logs exist
- **WHEN** backend code requests the dashboard aggregate and persisted `DataFetchLog` rows exist
- **THEN** the result includes recent fetch log summaries ordered newest first
- **AND** each summary includes fetch time, fetch mode, status, fetched row count, inserted row count, updated row count, and error summary

#### Scenario: No fetch logs exist
- **WHEN** backend code requests the dashboard aggregate and no `DataFetchLog` rows exist
- **THEN** the result includes an empty recent fetch log list

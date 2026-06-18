## ADDED Requirements

### Requirement: Data fetch log ORM model
The system SHALL define a `DataFetchLog` SQLAlchemy ORM model for market data fetch task logging.

#### Scenario: Model exposes fetch task fields
- **WHEN** backend code inspects the `DataFetchLog` model table
- **THEN** the table includes columns for `id`, `source`, `target_type`, `fetch_mode`, `range_start`, `range_end`, `requested_symbols`, `started_at`, `finished_at`, `status`, `rows_fetched`, `rows_inserted`, `rows_updated`, `error_message`, `created_at`, and `updated_at`

#### Scenario: Optional task fields are nullable
- **WHEN** backend code inspects the `DataFetchLog` model table
- **THEN** `range_start`, `range_end`, `requested_symbols`, `finished_at`, `rows_fetched`, `rows_inserted`, `rows_updated`, and `error_message` are nullable

### Requirement: Data fetch task status tracking
The system SHALL allow fetch logs to record whether a market data fetch task is running, succeeded, failed, or partially completed.

#### Scenario: Inspect allowed fetch statuses
- **WHEN** backend code creates fetch log rows for task lifecycle states
- **THEN** the model supports `running`, `success`, `failed`, and `partial` status values

#### Scenario: Record failed fetch error
- **WHEN** a fetch task fails with an error message
- **THEN** the fetch log can store the failure status and error message for later investigation

#### Scenario: Record partial fetch result
- **WHEN** a fetch task completes for only part of the requested range or symbol universe
- **THEN** the fetch log can store the partial status, result counts, and error message for later investigation

### Requirement: Full and incremental fetch scope logging
The system SHALL record enough fetch scope information to distinguish and investigate full and incremental market data fetches.

#### Scenario: Record full fetch scope
- **WHEN** a full market data fetch task is logged
- **THEN** the fetch log records the source, target type, full fetch mode, requested date range, and requested symbols

#### Scenario: Record incremental fetch scope
- **WHEN** an incremental market data fetch task is logged
- **THEN** the fetch log records the source, target type, incremental fetch mode, requested date range, and requested symbols

### Requirement: Data fetch log query indexes
The system SHALL define indexes that support market data fetch troubleshooting by source, status, target, fetch mode, and time range.

#### Scenario: Inspect data fetch log indexes
- **WHEN** backend code inspects the `DataFetchLog` model table indexes
- **THEN** indexes exist for querying logs by source, status, and start time, and for querying logs by target type, fetch mode, and requested date range

## ADDED Requirements

### Requirement: Trading calendar ORM model
The system SHALL define a `TradingCalendar` SQLAlchemy ORM model storing A-share trading days, with `trade_date` as the primary key.

#### Scenario: Model exposes trading day fields
- **WHEN** backend code inspects the `TradingCalendar` model table
- **THEN** the table includes columns for `trade_date`, `source`, `created_at`, and `updated_at`

#### Scenario: Trade date is the primary key
- **WHEN** backend code inspects the `TradingCalendar` model table
- **THEN** `trade_date` is the primary key, enforcing at most one row per trading day

### Requirement: Trading calendar akshare sync workflow
The system SHALL provide a sync workflow that fetches A-share trading days from akshare `tool_trade_date_hist_sina` and upserts them into the `trading_calendar` table.

#### Scenario: Sync fetches and upserts trading days
- **WHEN** the trading calendar sync workflow runs against a local database
- **THEN** the system fetches trading days from akshare `tool_trade_date_hist_sina`
- **AND** upserts each trading day into the `trading_calendar` table with `source` set to the provider name

#### Scenario: Sync is idempotent
- **WHEN** the trading calendar sync workflow runs repeatedly against the same database
- **THEN** repeated runs do not create duplicate `trading_calendar` rows
- **AND** existing trading days are updated in place rather than duplicated

#### Scenario: Sync reports counts
- **WHEN** the trading calendar sync workflow completes successfully
- **THEN** the system returns a result reporting the total synced count, inserted count, updated count, and a success status

#### Scenario: Sync failure is reported without crashing
- **WHEN** the akshare `tool_trade_date_hist_sina` call raises an exception
- **THEN** the sync returns a failed status with an error message describing the failure rather than propagating the exception

### Requirement: Trading calendar sync CLI command
The system SHALL provide a `vela sync-trading-calendar` CLI command that runs the trading calendar sync workflow against a local database.

#### Scenario: CLI sync command runs against a database URL
- **WHEN** a developer runs `vela sync-trading-calendar` with a `--database-url`
- **THEN** the system syncs the trading calendar into that database
- **AND** prints a summary of the inserted and updated counts

### Requirement: Trading calendar sync result
The system SHALL return a structured result from the trading calendar sync workflow.

#### Scenario: Result exposes sync counts and status
- **WHEN** backend code invokes the trading calendar sync workflow
- **THEN** the returned result includes total synced count, inserted count, updated count, and status

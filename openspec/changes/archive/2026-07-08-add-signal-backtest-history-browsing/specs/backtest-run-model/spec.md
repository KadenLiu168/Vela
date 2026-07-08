## MODIFIED Requirements

### Requirement: Backtest run ORM model
The system SHALL define a `BacktestRun` SQLAlchemy ORM model for one historical backtest execution.

#### Scenario: Model exposes backtest run fields
- **WHEN** backend code inspects the `BacktestRun` model table
- **THEN** the table includes columns for `id`, `strategy_id`, `config_version`, `start_date`, `end_date`, `parameters_json`, `started_at`, `finished_at`, `status`, `error_message`, `total_return`, `annualized_return`, `max_drawdown`, `sharpe_ratio`, `volatility`, `created_at`, and `updated_at`

#### Scenario: Backtest run status values
- **WHEN** backend code creates backtest run rows for execution lifecycle states
- **THEN** the model supports `running`, `success`, `failed`, and `partial` status values

#### Scenario: Optional run completion fields
- **WHEN** backend code inspects the `BacktestRun` model table
- **THEN** `finished_at`, `error_message`, `total_return`, `annualized_return`, `max_drawdown`, `sharpe_ratio`, and `volatility` are nullable

### Requirement: Backtest run history
The system SHALL preserve multiple backtest runs for the same strategy id, configuration version, and date range.

#### Scenario: Same strategy config and date range rerun
- **WHEN** two backtest run rows use the same `strategy_id`, `config_version`, `start_date`, and `end_date` values
- **THEN** the database allows both rows

#### Scenario: Inspect backtest run indexes
- **WHEN** backend code inspects the `BacktestRun` model table indexes
- **THEN** indexes exist for querying by strategy id and configuration version, by status and start timestamp, and by requested start and end date

### Requirement: Persist backtest results
The system SHALL persist a completed backtest result by creating a new `BacktestRun` row and related `BacktestEquityCurve` rows from caller-provided result data.

#### Scenario: Persist run metadata and metrics
- **WHEN** backend code persists a backtest result with strategy metadata, parameter JSON, lifecycle fields, and metric values
- **THEN** the database stores a new `BacktestRun` row with those values

#### Scenario: Persist equity curve rows
- **WHEN** backend code persists a backtest result with equity curve row inputs
- **THEN** the database stores `BacktestEquityCurve` rows linked to the newly created `BacktestRun`
- **AND** each curve row stores trade date, net value, cash, market value, total assets, and positions JSON

#### Scenario: Preserve rerun history
- **WHEN** backend code persists two backtest results for the same strategy id, configuration version, and date range
- **THEN** the database stores two separate `BacktestRun` rows

### Requirement: Export backtest report
The system SHALL export a human-readable report for a persisted backtest run selected by run id.

#### Scenario: Report core run fields
- **WHEN** backend code exports a report for an existing backtest run id
- **THEN** the report includes run id, strategy id, config version, date range, status, timestamps, and parameter JSON
- **AND** the report includes total return, annualized return, maximum drawdown, volatility, and Sharpe ratio

#### Scenario: Report equity curve summary
- **WHEN** backend code exports a report for a backtest run with equity curve rows
- **THEN** the report includes the equity curve point count
- **AND** the report includes the first and last curve rows
- **AND** the report includes the minimum and maximum net value rows

#### Scenario: Report empty equity curve
- **WHEN** backend code exports a report for a backtest run without equity curve rows
- **THEN** the report states that no equity curve rows are present

#### Scenario: Missing backtest run
- **WHEN** backend code exports a report for a run id that does not exist
- **THEN** the system raises a not-found error

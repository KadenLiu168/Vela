## ADDED Requirements

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
- **WHEN** backend code persists two backtest results for the same strategy name, configuration version, and date range
- **THEN** the database stores two separate `BacktestRun` rows

### Requirement: Query persisted backtest results
The system SHALL provide a query helper for retrieving a persisted backtest run with its equity curve rows.

#### Scenario: Load run with equity curve
- **WHEN** backend code queries a persisted backtest result by run id
- **THEN** the system returns the matching `BacktestRun`
- **AND** the run includes its related equity curve rows
- **AND** the equity curve rows are ordered by trade date and row id

#### Scenario: Missing run
- **WHEN** backend code queries a backtest run id that does not exist
- **THEN** the system returns no result

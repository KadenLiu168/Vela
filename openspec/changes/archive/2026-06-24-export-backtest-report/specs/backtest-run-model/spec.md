## ADDED Requirements

### Requirement: Export backtest report
The system SHALL export a human-readable report for a persisted backtest run selected by run id.

#### Scenario: Report core run fields
- **WHEN** backend code exports a report for an existing backtest run id
- **THEN** the report includes run id, strategy name, config version, date range, status, timestamps, and parameter JSON
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

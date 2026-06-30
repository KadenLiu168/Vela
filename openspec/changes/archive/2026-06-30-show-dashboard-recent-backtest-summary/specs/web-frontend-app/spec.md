## ADDED Requirements

### Requirement: Dashboard recent backtest summary states
The web frontend SHALL render the Dashboard recent backtest panel from the dashboard aggregate response with populated and empty states.

#### Scenario: Dashboard shows recent backtest summary
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is present
- **THEN** the backtest panel shows the backtest date range
- **AND** it shows the backtest status
- **AND** it shows total return, maximum drawdown, and Sharpe ratio summary values

#### Scenario: Dashboard shows empty recent backtest state
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is null
- **THEN** the backtest panel shows a clear empty state indicating that no backtest run has been recorded yet
- **AND** it shows a run-backtest entry point
- **AND** it does not treat the successful dashboard aggregate response as an API failure

#### Scenario: Dashboard recent backtest summary is backed by real API data
- **WHEN** dashboard validation exercises `GET /api/dashboard` against a local SQLite database with a persisted `BacktestRun` row
- **THEN** the returned recent backtest summary provides date range, status, total return, maximum drawdown, and Sharpe ratio values that the Dashboard page renders
- **AND** the validation does not rely only on frontend mock data

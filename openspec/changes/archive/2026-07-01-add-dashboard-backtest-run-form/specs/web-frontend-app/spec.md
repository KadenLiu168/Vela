## ADDED Requirements

### Requirement: Dashboard run backtest action
The web frontend SHALL let users run a backtest from the Dashboard for an explicit date range through the shared frontend API client.

#### Scenario: User submits a valid backtest date range
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user enters `2026-01-01` as the start date and `2026-01-31` as the end date
- **AND** the user submits the run-backtest action
- **THEN** the frontend sends `POST /api/backtests/run?startDate=2026-01-01&endDate=2026-01-31` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate backtest submissions while the request is pending

#### Scenario: Dashboard validates backtest date format
- **WHEN** the user enters a start date or end date that is not a valid `YYYY-MM-DD` date
- **AND** the user submits the run-backtest action
- **THEN** the Dashboard shows a concise validation error
- **AND** no run-backtest API request is sent

#### Scenario: Dashboard validates backtest date ordering
- **WHEN** the user enters a start date later than the end date
- **AND** the user submits the run-backtest action
- **THEN** the Dashboard shows a concise validation error
- **AND** no run-backtest API request is sent

#### Scenario: Dashboard shows scoped backtest submission feedback
- **WHEN** the run-backtest API request succeeds
- **THEN** the Dashboard shows a scoped operation status indicating that the backtest run was submitted
- **AND** it does not add a backtest detail link
- **AND** it does not show the submitted run result summary
- **AND** it does not rely on mocked backtest results as the only validation path

#### Scenario: Run backtest validation uses local API and SQLite
- **WHEN** frontend validation runs against a local FastAPI service configured with SQLite and sufficient market data
- **THEN** the validation can trigger `POST /api/backtests/run` through the shared frontend API client
- **AND** the backend persists the expected `BacktestRun` and `BacktestEquityCurve` rows through the existing backtest workflow
- **AND** the validation does not rely only on frontend mock data

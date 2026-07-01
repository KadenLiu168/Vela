## ADDED Requirements

### Requirement: Dashboard recent backtest refresh
The web frontend SHALL refresh the Dashboard recent backtest summary from the backend Dashboard API after a successful Dashboard backtest submission.

#### Scenario: Successful backtest refreshes recent summary
- **WHEN** a user submits a valid Dashboard backtest date range
- **AND** `POST /api/backtests/run` succeeds
- **THEN** the frontend requests the Dashboard aggregate from `GET /api/dashboard`
- **AND** the Recent backtest panel renders the backend-persisted recent backtest summary returned by that Dashboard aggregate
- **AND** the Operations panel continues to render the immediate run response summary

#### Scenario: Browser refresh restores recent backtest summary
- **WHEN** the Dashboard route loads after a browser refresh
- **AND** `GET /api/dashboard` returns a persisted recent backtest summary
- **THEN** the Recent backtest panel renders that persisted summary without requiring another run-backtest action

#### Scenario: Failed backtest does not refresh recent summary
- **WHEN** a valid Dashboard backtest submission fails with an HTTP or network error
- **THEN** the Operations panel shows a concise operation-level backtest error summary
- **AND** the frontend does not issue an additional Dashboard aggregate refresh for that failed run
- **AND** it does not render a stale successful run response summary

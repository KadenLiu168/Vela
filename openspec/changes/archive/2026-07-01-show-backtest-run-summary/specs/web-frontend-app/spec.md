## ADDED Requirements

### Requirement: Dashboard backtest run result summary
The web frontend SHALL render the result returned by the run backtest API after a successful Dashboard backtest submission.

#### Scenario: Dashboard shows successful backtest run summary
- **WHEN** a user submits a valid Dashboard backtest date range
- **AND** `POST /api/backtests/run` returns a successful JSON response
- **THEN** the Operations panel shows the returned run id
- **AND** it shows the returned status
- **AND** it shows the returned trading day count
- **AND** it shows the returned signal count
- **AND** it shows core metric summary values from the response

#### Scenario: Dashboard links to backtest detail after successful run
- **WHEN** the Dashboard renders a successful backtest run summary
- **THEN** the summary provides an entry point to `/backtests/<run id>`

#### Scenario: Dashboard shows operation error for failed backtest run
- **WHEN** a valid Dashboard backtest submission fails with an HTTP or network error
- **THEN** the Operations panel shows a concise operation-level backtest error summary
- **AND** it does not render a successful run summary

#### Scenario: Backtest run validation uses real API response shape
- **WHEN** frontend validation exercises the run backtest client against a local FastAPI service
- **THEN** the response includes run id, status, trading day count, signal count, and core metric fields that the Dashboard summary renders
- **AND** the validation does not rely only on frontend mock data

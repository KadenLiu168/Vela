## ADDED Requirements

### Requirement: API recent backtest list endpoint
The API service SHALL expose `GET /api/backtests` as a read-only endpoint that returns recent persisted backtest runs.

#### Scenario: Recent backtest list returns persisted runs
- **WHEN** a client sends `GET /api/backtests`
- **THEN** the response status is 200
- **AND** the response includes a `runs` list derived from persisted `BacktestRun` rows
- **AND** each run includes run id, start date, end date, status, started timestamp, finished timestamp, total return, annualized return, maximum drawdown, volatility, and Sharpe ratio
- **AND** the runs are ordered by newest start timestamp with run id as the tie-breaker

#### Scenario: Recent backtest list supports limit
- **WHEN** a client sends `GET /api/backtests?limit=1`
- **THEN** the response status is 200
- **AND** the response includes no more than one run

#### Scenario: Recent backtest list returns empty list
- **WHEN** a client sends `GET /api/backtests` and no backtest runs exist
- **THEN** the response status is 200
- **AND** the response includes an empty `runs` list

### Requirement: API recent backtest list integration validation
The API recent backtest list endpoint SHALL be validated with the local API app, a temporary SQLite database, and real `BacktestRun` rows.

#### Scenario: List endpoint reads persisted SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing multiple `BacktestRun` rows
- **THEN** `GET /api/backtests` returns values derived from those persisted rows
- **AND** the validation does not rely only on mocked backtest list data

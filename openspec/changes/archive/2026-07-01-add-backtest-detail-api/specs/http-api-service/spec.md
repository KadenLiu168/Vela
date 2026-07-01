## ADDED Requirements

### Requirement: API backtest detail endpoint
The API service SHALL expose `GET /api/backtests/{run_id}` as a read-only endpoint that returns one persisted backtest run with its equity curve.

#### Scenario: Backtest detail returns persisted run data
- **WHEN** a client sends `GET /api/backtests/{run_id}` for an existing run
- **THEN** the response status is 200
- **AND** the response includes run metadata with run id, strategy name, config version, start date, end date, parameters JSON, status, error message, started timestamp, and finished timestamp
- **AND** the response includes metrics with total return, annualized return, maximum drawdown, volatility, and Sharpe ratio
- **AND** the response includes an `equity_curve` list derived from persisted `BacktestEquityCurve` rows

#### Scenario: Backtest detail orders equity curve by trade date
- **WHEN** a persisted run has multiple equity curve rows
- **THEN** `GET /api/backtests/{run_id}` returns the equity curve points ordered by trade date ascending

#### Scenario: Backtest detail returns stable not found error
- **WHEN** a client sends `GET /api/backtests/{run_id}` for a missing run id
- **THEN** the response status is 404
- **AND** the response body is a stable not-found error

### Requirement: API backtest detail integration validation
The API backtest detail endpoint SHALL be validated with the local API app, a temporary SQLite database, and real persisted `BacktestRun` and `BacktestEquityCurve` rows.

#### Scenario: Detail endpoint reads persisted SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing a `BacktestRun` and related `BacktestEquityCurve` rows
- **THEN** `GET /api/backtests/{run_id}` returns values derived from those persisted rows
- **AND** the validation does not rely only on mocked backtest detail data

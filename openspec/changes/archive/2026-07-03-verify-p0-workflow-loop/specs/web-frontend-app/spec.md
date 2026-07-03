## ADDED Requirements

### Requirement: Dashboard persisted detail entry points
The web frontend SHALL provide detail entry points from populated persisted Dashboard summaries after Dashboard data is loaded or refreshed.

#### Scenario: Dashboard latest signal summary links to signal detail
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose latest signal summary is present
- **THEN** the latest signal panel provides a detail entry point to the Signal Detail route
- **AND** the entry point remains available after a browser refresh that reloads persisted backend data

#### Scenario: Dashboard recent backtest summary links to backtest detail
- **WHEN** the Dashboard route receives a successful dashboard aggregate response whose recent backtest summary is present
- **THEN** the recent backtest panel provides a detail entry point to `/backtests/<run id>`
- **AND** the entry point remains available after a browser refresh that reloads persisted backend data

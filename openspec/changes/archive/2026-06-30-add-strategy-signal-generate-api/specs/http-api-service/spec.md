## ADDED Requirements

### Requirement: API strategy signal generation endpoint
The API service SHALL expose a strategy signal generation command endpoint at `POST /api/strategy-signals/generate`.

#### Scenario: Generate strategy signal for explicit date
- **WHEN** a client sends `POST /api/strategy-signals/generate?signalDate=2026-06-23`
- **THEN** the API calls the existing core `generate_strategy_signal` capability for `2026-06-23`
- **AND** the response status is 200
- **AND** the response includes signal id, signal date, config version, status, result, error message, and positions

#### Scenario: Generate strategy signal for latest local market date
- **WHEN** a client sends `POST /api/strategy-signals/generate` without `signalDate`
- **THEN** the API uses the latest local `MarketPrice.trade_date` as the signal date
- **AND** the API calls the existing core `generate_strategy_signal` capability for that date
- **AND** the response includes the generated signal fields and positions

#### Scenario: Reject missing local market date
- **WHEN** a client sends `POST /api/strategy-signals/generate` without `signalDate` and the local database has no market prices
- **THEN** the API rejects the request before running signal generation

#### Scenario: No JSON body schema
- **WHEN** a client calls the strategy signal generation endpoint
- **THEN** the endpoint accepts `signalDate` only as an optional query parameter

### Requirement: API strategy signal generation integration validation
The API strategy signal generation endpoint SHALL be validated with the local API app, a temporary SQLite database, and the existing backend signal generation workflow.

#### Scenario: Generate endpoint persists signal rows to SQLite
- **WHEN** an API integration test configures the app with a temporary SQLite database containing active ETF metadata and enough local market price history
- **AND** the client sends `POST /api/strategy-signals/generate`
- **THEN** the response contains values produced by the existing core generation workflow
- **AND** the generated `StrategySignal` and `StrategySignalPosition` rows are persisted in SQLite
- **AND** the validation does not rely only on mocked signal generation results

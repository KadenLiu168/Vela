## ADDED Requirements

### Requirement: API latest strategy signal structured endpoint
The API service SHALL expose `GET /api/strategy-signals/latest` as a read-only endpoint that returns the latest successful persisted strategy signal as structured JSON.

#### Scenario: Latest signal endpoint returns structured signal data
- **WHEN** a client sends `GET /api/strategy-signals/latest` and a successful persisted strategy signal exists
- **THEN** the response status is 200
- **AND** the response includes `has_signal: true`
- **AND** the response includes signal metadata with signal id, signal date, config version, generated timestamp, result, and fallback status
- **AND** the response includes target positions with ETF identity, target weight, rank, score, and per-position fallback status

#### Scenario: Latest signal endpoint returns stable empty state
- **WHEN** a client sends `GET /api/strategy-signals/latest` and no successful persisted strategy signal exists
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: false`
- **AND** the response body includes `signal: null`
- **AND** the response body includes an empty `positions` list

#### Scenario: Latest signal endpoint has no date filter
- **WHEN** a client calls the latest signal endpoint
- **THEN** the endpoint does not require or define a `signalDate` filter

### Requirement: API latest strategy signal integration validation
The API latest strategy signal endpoint SHALL be validated with the local API app, a temporary SQLite database, and real `StrategySignal` and `StrategySignalPosition` rows.

#### Scenario: Latest signal endpoint reads persisted SQLite rows
- **WHEN** an API integration test configures the app with a temporary SQLite database containing multiple persisted strategy signals and positions
- **THEN** `GET /api/strategy-signals/latest` returns the newest successful signal by generated timestamp and id tie-breaker
- **AND** it ignores failed, running, and partial signals
- **AND** it derives fallback status from persisted position rank and score values
- **AND** the validation does not rely only on mocked signal report data

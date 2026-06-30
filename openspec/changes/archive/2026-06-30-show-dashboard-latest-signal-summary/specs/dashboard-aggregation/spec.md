## MODIFIED Requirements

### Requirement: Dashboard aggregate read model
The system SHALL provide a core dashboard aggregation service that returns first-screen strategy, market data, latest successful signal, and backtest state in one read model.

#### Scenario: Aggregate dashboard state
- **WHEN** backend code requests the dashboard aggregate with a SQLAlchemy session and current application configuration
- **THEN** the result includes strategy summary data
- **AND** the result includes market data status
- **AND** the result includes latest successful signal summary data when a successful signal exists
- **AND** the result includes recent backtest summary data when a backtest exists

#### Scenario: Empty persisted workflow data
- **WHEN** backend code requests the dashboard aggregate and the local database has no market prices, successful signals, or backtests
- **THEN** the market data status reports zero price rows and zero covered ETFs
- **AND** the latest signal summary is null
- **AND** the recent backtest summary is null

### Requirement: Dashboard latest signal summary
The dashboard aggregation service SHALL summarize the latest successful persisted strategy signal for first-screen review.

#### Scenario: Latest successful signal exists
- **WHEN** multiple persisted strategy signals exist
- **THEN** the latest signal summary uses the successful signal with the newest generated timestamp and id tie-breaker
- **AND** it ignores failed, running, and partial signals
- **AND** it includes signal id, signal date, config version, status, result, generated timestamp, fallback status, and position count

#### Scenario: Latest successful signal does not exist
- **WHEN** persisted strategy signals exist but none have success status
- **THEN** the latest signal summary is null

#### Scenario: Latest signal fallback status
- **WHEN** the latest successful signal has a persisted position without rank and score values
- **THEN** the latest signal summary marks fallback status as active

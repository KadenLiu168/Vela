## ADDED Requirements

### Requirement: Signal generation display loop validation
The repository SHALL include automated pytest coverage for the COP-125 signal generation to frontend display data-source loop.

#### Scenario: Pytest validates signal generation display loop
- **WHEN** a developer runs the API strategy signal generation tests through pytest
- **THEN** pytest MUST execute a test that triggers the signal generation API using deterministic SQLite market data
- **AND** the test MUST verify persisted `StrategySignal` and `StrategySignalPosition` rows
- **AND** the test MUST verify follow-up latest signal and Dashboard API responses reflect the same generated signal result

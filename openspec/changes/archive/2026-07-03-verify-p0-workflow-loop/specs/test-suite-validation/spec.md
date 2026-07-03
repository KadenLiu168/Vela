## ADDED Requirements

### Requirement: Full P0 workflow validation
The repository SHALL include automated pytest coverage for the COP-127 full P0 user workflow data-source loop.

#### Scenario: Pytest validates full P0 workflow loop
- **WHEN** a developer runs the API workflow tests through pytest
- **THEN** pytest MUST execute a test that reads Dashboard state, triggers market data fetch, triggers signal generation, triggers backtest execution, and reads backtest detail through real API endpoints
- **AND** the test MUST use deterministic SQLite data and existing backend workflows
- **AND** the test MUST verify follow-up API reads restore the persisted market data, signal, backtest, and detail state

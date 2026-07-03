## ADDED Requirements

### Requirement: Backtest run detail loop validation
The repository SHALL include automated pytest coverage for the COP-126 backtest run to detail display data-source loop.

#### Scenario: Pytest validates backtest run detail loop
- **WHEN** a developer runs the API backtest tests through pytest
- **THEN** pytest MUST execute a test that triggers the run-backtest API using deterministic SQLite market data
- **AND** the test MUST verify persisted `BacktestRun` and `BacktestEquityCurve` rows
- **AND** the test MUST verify a follow-up backtest detail API response reflects the same generated run metrics and equity curve rows

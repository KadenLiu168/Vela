## ADDED Requirements

### Requirement: Backtest Detail exposes derived return stability
`GET /api/backtests/{run_id}` SHALL include required `return_stability` metadata plus strategy and ordered fixed-benchmark rolling/monthly/yearly series derived by the shared core capability. Decimal values SHALL be six-place strings; dates/periods, counts, requested-scope partial flags, rolling status, and Sharpe status SHALL be typed explicitly. The router MUST NOT recalculate financial values.

#### Scenario: Detail returns exact core-derived series
- **WHEN** a persisted benchmark-enabled run has valid curves and sufficient observations
- **THEN** the response contains strategy and both benchmark series in stable benchmark order
- **AND** every value, date, count, status, and partial flag equals the core result

#### Scenario: Empty or short curve returns explicit empty state
- **WHEN** a valid run has an empty curve or fewer than 64 points
- **THEN** the response returns the appropriate typed status and empty rolling array
- **AND** does not fabricate zeros or omit the required stability object

#### Scenario: Corrupt curve has no partial detail
- **WHEN** persisted strategy or benchmark curve evidence violates the stability contract
- **THEN** the endpoint returns the standard error envelope and no partial Backtest Detail

### Requirement: Other backtest payloads remain unchanged
Backtest list and run-creation responses SHALL NOT include return-stability series, and the detail endpoint SHALL derive them only for the requested run without mutating or duplicating persisted data.

#### Scenario: List response remains bounded
- **WHEN** a client requests the backtest list after this Change
- **THEN** its existing item schema and curve-loading behavior remain unchanged

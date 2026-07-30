## ADDED Requirements

### Requirement: Deterministic official-session price series

The integration test support layer SHALL provide deterministic provider-shaped price series that can drive real strategy signal generation and backtest execution without external network access.

#### Scenario: Controlled series align with official sessions

- **WHEN** a workflow test requests provider rows for a fixed set of ETF identities and official trading sessions
- **THEN** the generated `DailyPrice` rows MUST use exactly those sessions
- **AND** the generated rows MUST NOT depend on weekends, `date.today()`, randomness, or external market data
- **AND** every active test ETF required by the workflow MUST have a complete row for every required eligible session

#### Scenario: Controlled provider preserves request bounds

- **WHEN** a workflow calls the controlled market-data provider with a symbol, optional start date, and optional end date
- **THEN** the provider MUST record the complete `(symbol, start_date, end_date)` request
- **AND** it MUST return only rows whose trade dates fall within the supplied inclusive bounds
- **AND** tests that invoke incremental fetch MUST fix the current-date boundary instead of deriving an expected end date from the wall clock

#### Scenario: Controlled series distinguish strategy outcomes

- **WHEN** the controlled data is used with the test-owned dual-momentum configuration
- **THEN** the configured risk assets MUST have distinguishable deterministic performance paths
- **AND** the expected selected ETF identities and ranking order MUST be derivable from the fixture definition
- **AND** one known-unselected provider series MUST use the same non-unit adjustment factor on every date so mapping and persisted factor precision are exercised without changing its return ratios

### Requirement: Production-shaped backtest position fixtures

Shared integration fixtures for persisted backtest equity rows SHALL use the same position object schema produced by the backtest runner.

#### Scenario: Shared equity row contains production position keys

- **WHEN** `equity_curve_row` or the shared workflow dataset creates a non-empty `positions_json`
- **THEN** the JSON MUST decode to an array of position objects
- **AND** every position object MUST contain `etf_id`, `target_weight`, and `actual_weight`
- **AND** weight values MUST use the production decimal-string representation
- **AND** the shared fixture MUST NOT substitute legacy `symbol` and `weight` keys

### Requirement: Test-owned canonical workflow inputs

The integration test support layer SHALL support a canonical pipeline workflow with a validated strategy configuration, matching ETF pool, official sessions, and controlled provider rows owned by the test.

#### Scenario: Canonical inputs are internally consistent

- **WHEN** the canonical core pipeline test prepares its workflow inputs
- **THEN** every strategy defense identity MUST exist in the matching ETF pool
- **AND** expected ETF membership and identifiers MUST derive from the test-owned configuration objects
- **AND** the strategy configuration MUST use fixed, non-zero, short lookback windows and enough official sessions to exercise more than one rebalance date
- **AND** legitimate edits to checked-in production strategy or ETF-pool configuration MUST NOT change the canonical workflow's signal schedule or expected identities

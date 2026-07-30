# integration-test-data Specification

## Purpose
Defines the reusable integration-test data layer: a prepared SQLite database with the current ORM schema plus a deterministic minimal workflow dataset for API and frontend acceptance.
## Requirements
### Requirement: SQLite integration database preparation
The test support layer SHALL provide a reusable way to initialize a temporary or local SQLite database with the current ORM schema for integration validation.

#### Scenario: Temporary SQLite database is initialized
- **WHEN** an integration test requests a prepared SQLite database URL
- **THEN** the database MUST contain the current ORM tables
- **AND** the caller MUST receive a SQLAlchemy session factory for inspecting persisted rows

#### Scenario: Local SQLite database can be prepared for API acceptance
- **WHEN** a developer prepares a local SQLite database for API or frontend acceptance validation
- **THEN** the preparation flow MUST create or replace the SQLite schema at the requested database URL
- **AND** the prepared database MUST be usable by the local API service through the shared database URL configuration path

### Requirement: Minimal workflow dataset
The integration data preparation flow SHALL provide a deterministic minimal dataset covering ETF metadata, market prices, latest strategy signal data, and recent backtest data.

#### Scenario: Workflow data is seeded
- **WHEN** the workflow dataset is prepared in SQLite
- **THEN** the database MUST contain active ETF metadata rows
- **AND** it MUST contain enough market price history for signal generation and backtest execution validation
- **AND** it MUST contain persisted strategy signal and position rows for latest signal validation
- **AND** it MUST contain persisted backtest run and equity curve rows for backtest list, detail, and dashboard validation

### Requirement: Provider and persistence boundary
The integration data preparation flow SHALL make clear which integration validations use a controlled provider and which validations must use persisted SQLite rows.

#### Scenario: Market data fetch uses controlled provider
- **WHEN** an integration test validates market data fetch behavior
- **THEN** it MAY use a controlled market data provider
- **AND** it MUST verify resulting `MarketPrice` and `DataFetchLog` rows persisted to SQLite

#### Scenario: Read and workflow validations use persistence
- **WHEN** integration validation covers dashboard, latest signal, backtest list, backtest detail, signal generation, or backtest execution
- **THEN** the validation MUST use real SQLite persistence paths
- **AND** it MUST NOT rely only on frontend request mocks or mocked workflow return values

### Requirement: Reusable API and frontend acceptance setup
The integration data preparation flow SHALL be reusable by API tests and by frontend API acceptance validation.

#### Scenario: API tests reuse shared setup
- **WHEN** API integration tests need local workflow data
- **THEN** they MUST be able to prepare that data through shared test-support helpers instead of duplicating endpoint-local schema and seed functions

#### Scenario: Frontend API validation uses prepared backend state
- **WHEN** frontend API integration validation runs against a local FastAPI service
- **THEN** the validation path MUST document how to prepare the SQLite database before starting the API
- **AND** it MUST exercise API client calls against backend state prepared by the shared integration data flow

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

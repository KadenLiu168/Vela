# test-suite-validation Specification

## Purpose
Defines the required passing quality gates for the repository: full pytest suite, Ruff lint, Ruff format check, and a CLI smoke validation.
## Requirements
### Requirement: Full pytest suite passes
The repository SHALL provide a passing full pytest suite through the configured `uv run pytest` command.

#### Scenario: Full suite validation succeeds
- **WHEN** a developer runs `uv run pytest` from the repository root
- **THEN** pytest MUST collect and execute the configured test suite without failures or errors

### Requirement: Ruff lint check passes
The repository SHALL provide a passing Ruff lint check through the configured `uv run ruff check .` command.

#### Scenario: Ruff lint validation succeeds
- **WHEN** a developer runs `uv run ruff check .` from the repository root
- **THEN** Ruff MUST complete without lint failures or errors

### Requirement: Ruff format check passes
The repository SHALL provide a passing Ruff format check through the configured `uv run ruff format --check .` command.

#### Scenario: Ruff format validation succeeds
- **WHEN** a developer runs `uv run ruff format --check .` from the repository root
- **THEN** Ruff MUST complete without reporting files that would be reformatted

### Requirement: CLI smoke validation passes
The repository SHALL provide a CLI smoke validation path that exercises the installed `vela` console script through `uv run`.

#### Scenario: CLI startup validation succeeds
- **WHEN** a developer runs the CLI smoke validation from the repository root
- **THEN** the validation MUST execute `uv run vela --help` successfully
- **AND** the validation MUST fail if the installed console script cannot import project packages

#### Scenario: CLI database initialization validation succeeds
- **WHEN** a developer runs the CLI smoke validation from the repository root
- **THEN** the validation MUST execute database initialization against a temporary SQLite database URL successfully
- **AND** the validation MUST not depend on manually setting `PYTHONPATH`

### Requirement: Shared integration data validation
The repository SHALL validate that shared integration test data setup can initialize SQLite and seed the minimal workflow dataset.

#### Scenario: Integration data setup is tested
- **WHEN** the Python test suite runs
- **THEN** it MUST validate that the shared integration data setup creates ORM tables and persists ETF, market price, strategy signal, and backtest rows in SQLite

### Requirement: Frontend API integration preparation path
The repository SHALL document a frontend API integration validation path that prepares SQLite backend state before frontend API client tests call the local FastAPI service.

#### Scenario: Frontend API integration path is documented
- **WHEN** a developer follows the frontend API integration validation documentation
- **THEN** they MUST be able to prepare deterministic local SQLite data before running `npm --prefix apps/web run test:integration:api`
- **AND** the documented flow MUST distinguish controlled provider validations from validations that require real persistence

### Requirement: API contract validation is part of pytest
The repository SHALL include API contract validation in the configured Python pytest suite.

#### Scenario: API contract tests run with pytest
- **WHEN** a developer runs `uv run pytest` from the repository root
- **THEN** pytest MUST collect and execute the API contract tests covering the Phase 1 API endpoint surface
- **AND** the tests MUST validate successful response structures, empty-data structures, and key error response envelopes

### Requirement: Frontend TypeScript validation passes
The repository SHALL provide a passing frontend TypeScript validation command through `npm --prefix apps/web run typecheck`.

#### Scenario: Frontend TypeScript validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run typecheck` from the repository root
- **THEN** TypeScript project build validation MUST complete without type errors
- **AND** the command MUST NOT require a running local API service or frontend mock service

### Requirement: Frontend production build validation passes
The repository SHALL provide a passing frontend production build validation command through `npm --prefix apps/web run build`.

#### Scenario: Frontend production build validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run build` from the repository root
- **THEN** the frontend production build MUST complete successfully
- **AND** the build MUST include TypeScript validation
- **AND** the command MUST NOT require a running local API service, seeded SQLite data, or frontend mock service

### Requirement: Frontend key component test validation

The repository SHALL include key frontend component-region validation in the configured frontend test suite.

#### Scenario: Frontend test suite validates key component regions

- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering Dashboard status blocks, target holdings tables, backtest metric cards, and error summaries with zero failures
- **AND** those tests MUST use controlled fixtures whose field names and nesting match the real API response structures consumed by the shared frontend API client

#### Scenario: Frontend test suite validates key component states

- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering loading, empty, and error states for the key frontend component regions with zero failures

#### Scenario: jsdom environment initializes reliably

- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** the vitest jsdom environment SHALL initialize consistently across repeated runs
- **AND** no test SHALL fail with `document is not defined`

#### Scenario: Coverage timeline test assertions match current DOM structure

- **WHEN** Dashboard mock data includes non-null `earliest_trade_date` and `latest_trade_date`
- **THEN** tests SHALL query the timeline labels as `"Earliest"` and `"Latest"` (not `"trade date"`)
- **AND** when dates are null, tests SHALL verify the timeline is not rendered

### Requirement: Market data fetch dashboard loop validation
The repository SHALL include automated pytest coverage for the COP-124 market data fetch to Dashboard closed loop.

#### Scenario: Pytest validates market data fetch dashboard loop
- **WHEN** a developer runs the API market data fetch tests through pytest
- **THEN** pytest MUST execute a test that triggers the market data fetch API with a controlled provider
- **AND** the test MUST verify persisted `MarketPrice` and `DataFetchLog` rows
- **AND** the test MUST verify a follow-up Dashboard API response reflects the newly persisted market data status and fetch operation summary

### Requirement: Signal generation display loop validation
The repository SHALL include automated pytest coverage for the COP-125 signal generation to frontend display data-source loop.

#### Scenario: Pytest validates signal generation display loop
- **WHEN** a developer runs the API strategy signal generation tests through pytest
- **THEN** pytest MUST execute a test that triggers the signal generation API using deterministic SQLite market data
- **AND** the test MUST verify persisted `StrategySignal` and `StrategySignalPosition` rows
- **AND** the test MUST verify follow-up latest signal and Dashboard API responses reflect the same generated signal result

### Requirement: Backtest run detail loop validation
The repository SHALL include automated pytest coverage for the COP-126 backtest run to detail display data-source loop.

#### Scenario: Pytest validates backtest run detail loop
- **WHEN** a developer runs the API backtest tests through pytest
- **THEN** pytest MUST execute a test that triggers the run-backtest API using deterministic SQLite market data
- **AND** the test MUST verify persisted `BacktestRun` and `BacktestEquityCurve` rows
- **AND** the test MUST verify a follow-up backtest detail API response reflects the same generated run metrics and equity curve rows

### Requirement: Full P0 workflow validation
The repository SHALL include automated pytest coverage for the COP-127 full P0 user workflow data-source loop.

#### Scenario: Pytest validates full P0 workflow loop
- **WHEN** a developer runs the API workflow tests through pytest
- **THEN** pytest MUST execute a test that reads Dashboard state, triggers market data fetch, triggers signal generation, triggers backtest execution, and reads backtest detail through real API endpoints
- **AND** the test MUST use deterministic SQLite data and existing backend workflows
- **AND** the test MUST verify follow-up API reads restore the persisted market data, signal, backtest, and detail state

### Requirement: Tests assert contracts over configuration snapshots

The test suite SHALL verify behavior contracts rather than encode point-in-time configuration snapshots. Assertions that depend on mutable configuration (ETF pool membership counts, `strategy_id` literal values, dashboard response field sets) SHALL derive expected values from the loaded configuration or the production aggregation output at test time, not from hardcoded literals copied from a past state. This keeps the suite green across legitimate configuration and response-shape evolution, and fails fast only when a contract is genuinely broken.

#### Scenario: Configuration-loading tests derive counts from the loaded source

- **WHEN** a test verifies that a YAML configuration loader returns a typed config object
- **THEN** the test asserts the loader parses the checked-in YAML into the expected typed structure
- **AND** any count assertion (for example ETF pool size) derives the expected count from the loaded configuration or the source YAML at test time
- **AND** the test does not hardcode a literal count that drifts when the configuration is legitimately expanded

#### Scenario: Pass-through identity tests use the loaded config value

- **WHEN** a test verifies that a configured identifier (for example `strategy_id`) is passed through an endpoint or persistence layer unchanged
- **THEN** the test sources the expected identifier from the loaded `AppConfig`
- **AND** the test does not hardcode a literal identifier value that drifts when the configuration value is legitimately changed

#### Scenario: Response-shape tests match the production aggregation output

- **WHEN** a test asserts the exact shape of an API response built by a production aggregation module
- **THEN** the test's expected fixture includes every field the production aggregation module emits for the seeded data
- **AND** the test does not omit a field that production already produces and the frontend already consumes


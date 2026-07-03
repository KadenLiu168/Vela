# test-suite-validation Specification

## Purpose
TBD - created by archiving change validate-pytest-suite-passes. Update Purpose after archive.
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
- **THEN** Vitest MUST execute frontend tests covering Dashboard status blocks, target holdings tables, backtest metric cards, and error summaries
- **AND** those tests MUST use controlled fixtures whose field names and nesting match the real API response structures consumed by the shared frontend API client

#### Scenario: Frontend test suite validates key component states
- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering loading, empty, and error states for the key frontend component regions

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


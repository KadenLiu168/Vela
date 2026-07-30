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
The repository SHALL include automated pytest coverage for the COP-127 full P0 user workflow data-source loop. This API workflow SHALL complement the canonical core pipeline by validating transport delegation, serialization, persistence readback, and Dashboard linkage without duplicating focused financial arithmetic or the canonical core workflow's complete synchronization and rerun assertions.

#### Scenario: Pytest validates full P0 workflow loop
- **WHEN** a developer runs the API workflow tests through pytest
- **THEN** pytest MUST execute a test that reads Dashboard state, triggers market data fetch, triggers signal generation, triggers backtest execution, and reads backtest detail through real API endpoints
- **AND** the test MUST use deterministic SQLite data, a validated test-owned strategy configuration, controlled source responses, and existing backend workflows
- **AND** the test MUST verify follow-up API reads restore the persisted market data, signal, backtest, and detail state
- **AND** the test MUST verify serialized signal identities, ranks, and weights and production-shaped equity-curve `positions_json`
- **AND** the test MUST verify Dashboard state links to the generated fetch, the latest successful signal under production ordering, and the recent backtest run
- **AND** the earlier manual signal MUST remain independently readable and unlinked to the backtest

#### Scenario: P0 assertions remain transport-focused

- **WHEN** the P0 API workflow verifies a completed backtest
- **THEN** response metric values MUST match the corresponding persisted run values
- **AND** the workflow MUST retain unique HTTP status, response-shape, and read-after-write assertions
- **AND** trading-day and signal-count assertions MUST be derived from controlled official sessions and linked/detail collections rather than hardcoded natural-day counts or existence-only checks
- **AND** controlled provider request assertions MUST retain deterministic symbol ordering and include fixed start and end bounds
- **AND** it MUST NOT pin exact financial metric goldens or duplicate the canonical core workflow's full rerun-isolation proof

### Requirement: Canonical ingestion-to-quant core contract validation

The repository SHALL include one canonical pytest workflow that exercises the real ingestion-to-quant core contracts against a temporary file-backed SQLite database using controlled external-source responses.

#### Scenario: Canonical workflow reaches persisted read models

- **WHEN** the canonical core pipeline test runs
- **THEN** it MUST initialize the temporary database exclusively through Alembic migration to head
- **AND** it MUST NOT call ORM `create_all` for the canonical database
- **AND** it MUST call the real ETF pool and trading-calendar synchronization services
- **AND** it MUST call the real full market-data fetch service with a controlled provider
- **AND** it MUST verify provider-shaped close prices and a non-unit factor are persisted at the model's declared precision
- **AND** it MUST call the real live signal service and real backtest runner without replacing strategy generation, equity calculation, or metric calculation
- **AND** it MUST read the persisted run through the backtest result service and Dashboard aggregation service

#### Scenario: Canonical stages exchange committed state

- **WHEN** the canonical workflow advances from migration through synchronization, fetch, signal, backtest, and readback
- **THEN** the engine and session factory MUST be created after Alembic migration completes
- **AND** each major service stage MUST finish through its existing production transaction boundary, using caller-managed sessions where the core service does not commit
- **AND** the next stage MUST use a fresh session to consume committed database state
- **AND** the test MUST NOT add commits inside core functions whose transaction is caller-managed

#### Scenario: Live and backtest signal branches remain distinct

- **WHEN** a manual signal is generated before the canonical backtest executes
- **THEN** the manual signal MUST remain unlinked to the backtest run
- **AND** the backtest MUST persist its own historical signals with `source="backtest"`
- **AND** the run's linked signal IDs and equity calculation MUST be scoped only to signals generated for that run

#### Scenario: Real reruns remain isolated

- **WHEN** the canonical workflow runs the same test-owned strategy and date range a second time through the real backtest runner
- **THEN** the two runs' linked signal ID sets MUST be disjoint
- **AND** the first run's persisted signals, equity curve, metrics, and data snapshot MUST remain unchanged
- **AND** the two runs' complete `data_snapshot_json` values, including `data_checksum`, MUST be equal because their persisted market inputs are equal
- **AND** both runs MUST remain independently readable

#### Scenario: Canonical assertions divide structural and arithmetic responsibilities

- **WHEN** the canonical workflow validates a successful backtest
- **THEN** it MUST assert deterministic selected identities, ranking and weight invariants, persisted linkage, result structure, and readback equality
- **AND** it MUST NOT replace the focused core tests responsible for exact momentum, trend, equity, cost, and performance-metric arithmetic

### Requirement: Network-independent backend workflow validation

Backend workflow tests SHALL remain deterministic and SHALL NOT require live Tencent or akshare access.

#### Scenario: Pytest workflow uses controlled source boundaries

- **WHEN** the canonical core or P0 API workflow runs under pytest
- **THEN** the workflow MUST inject a controlled market-data provider instead of constructing a real network provider
- **AND** trading-calendar synchronization MUST import an in-process fake `akshare` module whose fixed DataFrame response contains no network operation
- **AND** provider calls MUST be inspectable through their recorded symbol and date bounds
- **AND** no subprocess CLI fetch/calendar pipeline SHALL be required by this change

### Requirement: Tests assert contracts over configuration snapshots

The test suite SHALL verify behavior contracts rather than encode point-in-time configuration snapshots. Assertions that depend on mutable configuration (ETF pool membership counts, strategy parameters, configured identifiers, and serialized strategy groups) SHALL derive expected values from the loaded configuration or the production aggregation output at test time, not from hardcoded literals copied from a past state. Tests that execute a deterministic workflow SHALL inject an explicit test-owned configuration when mutable production configuration is not the subject under test. Exact financial arithmetic SHALL remain covered by focused core tests with controlled inputs rather than by unrelated API orchestration goldens.

#### Scenario: Configuration-loading tests derive mutable values from the loaded source

- **WHEN** a test verifies that a checked-in YAML configuration loader returns a typed config object
- **THEN** the test asserts the loader parses the checked-in YAML into the expected typed structure
- **AND** mutable parameter and count assertions derive their expected values from the loaded configuration or source YAML at test time
- **AND** the test does not hardcode a point-in-time parameter or count that drifts when the configuration is legitimately revised

#### Scenario: Pass-through identity tests use the loaded config value

- **WHEN** a test verifies that a configured identifier is passed through an endpoint or persistence layer unchanged
- **THEN** the test sources the expected identifier from the loaded `AppConfig`
- **AND** the test does not hardcode a literal identifier value that drifts when the configuration value is legitimately changed

#### Scenario: Configuration API expected values are constructed independently

- **WHEN** a test verifies the strategy object returned by `/api/config`
- **THEN** the test derives mutable strategy values from the independently loaded typed application configuration
- **AND** the expected value is not produced by calling the same production serializer that produces the actual response
- **AND** the test still detects missing fields, unexpected fields, or incorrect serialization transformations

#### Scenario: Response-shape tests match the production aggregation output

- **WHEN** a test asserts the exact shape of an API response built by a production aggregation module
- **THEN** the test's expected fixture includes every field the production aggregation module emits for the seeded data
- **AND** the test does not omit a field that production already produces and the frontend already consumes

#### Scenario: API backtest workflows use a deterministic test configuration

- **WHEN** an API test executes the run-backtest endpoint using seeded SQLite market data
- **THEN** the test injects an explicit validated strategy configuration owned by the test
- **AND** the test configuration fixes all strategy, rebalance, cost, performance, and defense inputs needed by the scenario
- **AND** edits to the default checked-in production strategy configuration do not alter the test's signal schedule, fixtures, or metric path

#### Scenario: API metric assertions verify orchestration contracts

- **WHEN** an API workflow test verifies metrics produced by a completed backtest
- **THEN** it verifies the response metrics are present in their API representation
- **AND** it verifies the response values equal the corresponding persisted `BacktestRun` values
- **AND** it verifies applicable domain invariants such as `-1 < max_drawdown <= 0`
- **AND** it does not pin an exact derived metric unless that metric's arithmetic is the explicit subject of the test

#### Scenario: Core tests retain exact financial regression coverage

- **WHEN** focused core tests verify maximum drawdown or transaction-cost behavior
- **THEN** they use controlled curve, holding, price, and strategy configuration inputs
- **AND** they assert exact `Decimal` results for the financial contract
- **AND** transaction-cost coverage compares cost and no-cost behavior or otherwise proves the configured basis-point rate is applied

### Requirement: Frontend ESLint validation passes
The repository SHALL provide a passing frontend ESLint validation command through `npm --prefix apps/web run lint`.

#### Scenario: Frontend ESLint validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run lint` from the repository root
- **THEN** ESLint MUST complete without lint failures or errors
- **AND** the command MUST NOT require a running local API service or frontend mock service

### Requirement: Frontend CSS lint validation passes
The repository SHALL provide a passing frontend CSS lint validation command through `npm --prefix apps/web run lint:css`.

#### Scenario: Frontend CSS lint validation succeeds
- **WHEN** a developer runs `npm --prefix apps/web run lint:css` from the repository root
- **THEN** Stylelint MUST complete without lint failures or errors
- **AND** the command MUST enforce the design-system invariants without weakening existing rules

### Requirement: Python mypy validation passes

The repository SHALL provide a passing Python static type validation command through the configured mypy invocation.

#### Scenario: Python mypy validation succeeds

- **WHEN** a developer runs the configured mypy validation command from the repository root
- **THEN** mypy MUST check the configured Python source trees without type errors
- **AND** the command MUST use the repository's checked-in mypy configuration

### Requirement: Quality validation commands are CI-reusable

The repository SHALL keep quality validation commands executable from the repository root so local validation and CI validation exercise the same checks.

#### Scenario: Python validation commands run from repo root

- **WHEN** CI or a developer runs Python quality validation from the repository root
- **THEN** `uv run ruff check .`, `uv run ruff format --check .`, the configured mypy command, and `uv run pytest` MUST be executable without manually setting `PYTHONPATH`

#### Scenario: Frontend validation commands run from repo root

- **WHEN** CI or a developer runs frontend quality validation from the repository root
- **THEN** `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build` MUST be executable without requiring a running local API service

### Requirement: Tests must not hardcode machine-specific absolute paths

The test suite SHALL assert filesystem paths using repository-relative resolution or the same constants the production code uses, not hardcoded absolute paths tied to a specific developer machine or checkout location. Assertions that compare a resolved path (for example the CLI's default strategy config path) SHALL derive the expected value from the production constant or compute it relative to the repository root at test time, not from a literal absolute path copied from one environment. This keeps the suite green across machines and CI runners (which check the repo out at arbitrary paths), and fails fast only when a path-resolution contract is genuinely broken.

#### Scenario: CLI default-config-path test uses the production constant

- **WHEN** a test verifies that the CLI resolves its default strategy config path
- **THEN** the test asserts the captured path equals the CLI's `DEFAULT_STRATEGY_CONFIG_PATH` constant
- **AND** the test does not hardcode an absolute path such as `/Users/kaden/Vela/config/strategy_v1.yaml` that only matches when the repository is checked out at that exact location

#### Scenario: Suite passes on any checkout path

- **WHEN** the pytest suite runs on a CI runner or any machine regardless of checkout path
- **THEN** path-comparing tests MUST pass using the resolved, environment-independent path
- **AND** no test SHALL fail solely because the repository checkout directory differs from a hardcoded absolute path

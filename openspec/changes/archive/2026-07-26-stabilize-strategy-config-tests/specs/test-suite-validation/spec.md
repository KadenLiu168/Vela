## MODIFIED Requirements

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

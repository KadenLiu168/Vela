## ADDED Requirements

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

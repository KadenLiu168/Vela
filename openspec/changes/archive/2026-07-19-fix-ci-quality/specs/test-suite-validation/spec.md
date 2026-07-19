## ADDED Requirements

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

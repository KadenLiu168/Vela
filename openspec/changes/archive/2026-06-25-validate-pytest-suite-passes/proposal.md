## Why

COP-75 requires the repository's full pytest suite to pass as a Phase 1 backend acceptance gate. Capturing this as an OpenSpec change keeps the validation result traceable without expanding business functionality.

## What Changes

- Validate that `uv run pytest` passes for the configured full test suite.
- Document the repository-level pytest acceptance requirement as a test-suite validation capability.
- Do not change runtime behavior, public APIs, data models, migrations, or dependencies unless a failing test requires a minimal fix.

## Capabilities

### New Capabilities

- `test-suite-validation`: Defines the repository-level acceptance requirement for running the full pytest suite successfully.

### Modified Capabilities

- None.

## Impact

- Affected systems: test execution and OpenSpec documentation.
- Affected commands: `uv run pytest`, plus existing lint/typecheck/OpenSpec validation commands used during final verification.
- No expected production code, schema, CLI, API, or dependency changes.

## Why

COP-76 requires the repository's configured Ruff lint check to pass as a Phase 1 backend acceptance gate. Capturing this as an OpenSpec change keeps lint validation traceable without expanding runtime behavior.

## What Changes

- Validate that `uv run ruff check .` passes from the repository root.
- Extend the repository-level test-suite validation capability to include Ruff static lint checks.
- Do not change runtime behavior, public APIs, data models, migrations, dependencies, or formatting unless Ruff lint failures require a minimal fix.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `test-suite-validation`: Add a repository-level requirement that the configured Ruff lint command passes.

## Impact

- Affected systems: lint validation and OpenSpec documentation.
- Affected commands: `uv run ruff check .`, plus existing pytest, type check, and OpenSpec validation commands used during final verification.
- No expected production code, schema, CLI, API, or dependency changes.

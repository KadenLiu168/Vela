## Why

COP-77 closes the remaining repository validation gap discovered during COP-75 and COP-76: `uv run pytest` and `uv run ruff check .` pass, but `uv run ruff format --check .` still reports formatting drift. The project already documents Ruff formatting as a development command, so accepting Ruff's default formatting makes the validation gate consistent and keeps future formatting decisions low-maintenance.

## What Changes

- Validate that `uv run ruff format --check .` passes from the repository root.
- Apply Ruff's default formatter output to the currently drifted files without changing runtime behavior.
- Document Ruff format validation as part of the existing repository-level validation capability.
- Do not adjust Ruff configuration, line length, dependencies, business logic, public APIs, data models, migrations, or historical archive records.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite-validation`: Add a repository requirement that the configured Ruff format check passes through `uv run ruff format --check .`.

## Impact

- Affected code: formatting-only edits in Python files currently reported by `uv run ruff format --check .`.
- Affected specs: extend `test-suite-validation`.
- Affected commands: `uv run ruff format --check .`, plus existing lint, pytest, type check, and OpenSpec validation commands used during final verification.
- APIs, dependencies, database schema, and runtime behavior: no changes.

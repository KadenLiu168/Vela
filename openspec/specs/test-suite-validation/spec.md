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


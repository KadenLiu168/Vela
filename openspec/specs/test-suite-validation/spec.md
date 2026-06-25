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


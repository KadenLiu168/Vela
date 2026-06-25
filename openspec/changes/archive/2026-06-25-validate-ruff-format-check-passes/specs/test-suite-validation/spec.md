## ADDED Requirements

### Requirement: Ruff format check passes
The repository SHALL provide a passing Ruff format check through the configured `uv run ruff format --check .` command.

#### Scenario: Ruff format validation succeeds
- **WHEN** a developer runs `uv run ruff format --check .` from the repository root
- **THEN** Ruff MUST complete without reporting files that would be reformatted

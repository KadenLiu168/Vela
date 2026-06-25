## ADDED Requirements

### Requirement: Ruff lint check passes
The repository SHALL provide a passing Ruff lint check through the configured `uv run ruff check .` command.

#### Scenario: Ruff lint validation succeeds
- **WHEN** a developer runs `uv run ruff check .` from the repository root
- **THEN** Ruff MUST complete without lint failures or errors

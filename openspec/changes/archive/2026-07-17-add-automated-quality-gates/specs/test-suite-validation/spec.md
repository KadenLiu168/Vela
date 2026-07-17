## ADDED Requirements

### Requirement: Python mypy validation passes

The repository SHALL provide a passing Python static type validation command through the configured mypy invocation.

#### Scenario: Python mypy validation succeeds

- **WHEN** a developer runs the configured mypy validation command from the repository root
- **THEN** mypy MUST check the configured Python source trees without type errors
- **AND** the command MUST use the repository's checked-in mypy configuration

### Requirement: Quality validation commands are CI-reusable

The repository SHALL keep quality validation commands executable from the repository root so local validation and CI validation exercise the same checks.

#### Scenario: Python validation commands run from repo root

- **WHEN** CI or a developer runs Python quality validation from the repository root
- **THEN** `uv run ruff check .`, `uv run ruff format --check .`, the configured mypy command, and `uv run pytest` MUST be executable without manually setting `PYTHONPATH`

#### Scenario: Frontend validation commands run from repo root

- **WHEN** CI or a developer runs frontend quality validation from the repository root
- **THEN** `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build` MUST be executable without requiring a running local API service

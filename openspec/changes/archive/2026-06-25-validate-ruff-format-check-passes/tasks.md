## 1. Confirm Formatting Drift

- [x] 1.1 Run `uv run ruff format --check .` from the repository root and confirm the current drifted file list.
- [x] 1.2 Review `uv run ruff format --diff .` output to confirm the expected changes are formatting-only.

## 2. Apply Ruff Formatting

- [x] 2.1 Run Ruff formatting using the repository's configured environment.
- [x] 2.2 Review the resulting git diff and confirm it does not include business logic, API, data model, migration, dependency, or configuration changes.

## 3. Validate

- [x] 3.1 Run `uv run ruff format --check .`.
- [x] 3.2 Run `uv run ruff check .`.
- [x] 3.3 Run `uv run pytest`.
- [x] 3.4 Run `uv run mypy apps/cli/src packages/core/src`.
- [x] 3.5 Run `openspec validate validate-ruff-format-check-passes --strict`.
- [x] 3.6 Run `openspec validate --all --strict`.

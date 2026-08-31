## 1. Reconfirm removal preconditions

- [x] 1.1 Search active source, tests, scripts, configuration, CI, and tooling for direct `numpy`, `pydantic-settings`, and `pytest-cov` usage; distinguish declarations, transitive lock entries, generated metadata, and historical records from operational requirements, and stop if a real direct requirement is found.

## 2. Remove stale direct dependency state

- [x] 2.1 Remove `numpy` and `pydantic-settings` from `[project].dependencies`, remove `pytest-cov` from the dev dependency group, and remove only `pydantic-settings` from the root README backend Tech Stack line; do not change executable source, tests, coverage policy, or unrelated documentation.
- [x] 2.2 Run `uv lock` to regenerate `uv.lock`, without manual edits, and inspect the dependency diff to confirm any retained NumPy is transitive and no unrelated dependency upgrade or pruning entered scope.

## 3. Verify behavior and scope

- [x] 3.1 Run `uv sync --group dev` successfully against the regenerated dependency state.
- [x] 3.2 Run `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 3.3 Recheck that the three direct declarations and all active direct imports/coverage options are absent; run `openspec validate remove-unused-python-dependencies --strict` and inspect the final diff to confirm only `pyproject.toml`, `uv.lock`, and the affected README wording changed, with no ECO-57, Web, database, archived-spec, or behavior changes.

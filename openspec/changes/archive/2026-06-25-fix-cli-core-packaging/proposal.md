## Why

The backend test suite is complete, but the documented CLI entrypoint is not runnable after a normal `uv sync` because the installed `vela` command cannot import `vela_core`. This blocks local validation of the completed backend from the same commands developers are expected to use.

## What Changes

- Fix project packaging so the installed `vela` console script can import both `vela_cli` and `vela_core` without manually setting `PYTHONPATH`.
- Add a focused verification path for CLI startup and database initialization through the installed project tooling.
- Keep the existing monorepo layout and avoid introducing a new service, API, or frontend scope.
- Link implementation work to Linear issue `COP-78`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli-database-initialization`: Clarify that the project CLI must be runnable from the normal uv-managed environment, not only under test-time `pythonpath`.
- `test-suite-validation`: Add CLI smoke validation for the installed console script and local database initialization.

## Impact

- Affected files: `pyproject.toml`, CLI packaging configuration, and focused validation tests or documentation if needed.
- Affected commands: `uv sync`, `uv run vela --help`, `uv run vela init-db --database-url ...`, `uv run pytest`, and `uv run ruff check .`.
- No database schema, business logic, API, or dependency changes are expected.

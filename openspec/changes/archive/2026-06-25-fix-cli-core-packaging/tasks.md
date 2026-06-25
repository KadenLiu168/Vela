## 1. Reproduce and Guard

- [x] 1.1 Confirm `uv run vela --help` fails in the current clean uv environment without manually setting `PYTHONPATH`.
- [x] 1.2 Add a focused CLI smoke validation that runs the installed `vela` console script through `uv run`.
- [x] 1.3 Include temporary SQLite database initialization in the smoke validation.

## 2. Packaging Fix

- [x] 2.1 Update `pyproject.toml` package discovery so both `vela_cli` and `vela_core` are installed from their existing source roots.
- [x] 2.2 Run `uv sync` to refresh editable install metadata.
- [x] 2.3 Verify `uv run python -c "import vela_cli; import vela_core"` succeeds without custom `PYTHONPATH`.

## 3. Verification

- [x] 3.1 Verify `uv run vela --help` succeeds without custom `PYTHONPATH`.
- [x] 3.2 Verify `uv run vela init-db --database-url sqlite+pysqlite:////tmp/vela-smoke.db` succeeds without custom `PYTHONPATH`.
- [x] 3.3 Run `uv run pytest`.
- [x] 3.4 Run `uv run ruff check .`.

## Why

`packages/core/src/vela_core/bootstrap.py` (a business orchestration module in the reusable core package) directly imports `alembic` and computes the project root via `Path(__file__).resolve().parents[4]` to locate the Alembic script directory. This couples the core business package to a migration tool and to a hardcoded directory layout — if the package is installed via pip/uv or the file moves, the path silently points to a nonexistent directory and migrations fail. The same `_build_alembic_config` + `command.upgrade` pattern is duplicated verbatim in `apps/cli/src/vela_cli/main.py` and `packages/core/tests/test_bootstrap.py` (three copies total).

## What Changes

- **New core module `vela_core/migration.py`**: provides `build_alembic_config(database_url, script_location) -> Config` and `run_alembic_upgrade(database_url, script_location) -> None` as the single place that imports `alembic`. Isolates the alembic dependency in a leaf infrastructure module.
- **`bootstrap.py` no longer imports `alembic`**: delegates step 1 (migrate) to `vela_core.migration.run_alembic_upgrade`. Removes `ROOT = parents[4]` and `DEFAULT_ALEMBIC_SCRIPT_LOCATION`.
- **BREAKING**: `run_local_setup_bootstrap`'s `script_location` parameter changes from optional (with `parents[4]` default) to **required**. Callers must pass it explicitly.
- **`apps/api/src/vela_api/config.py`**: adds `DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"` next to the existing `DEFAULT_STRATEGY_CONFIG_PATH` (same `parents[4]` pattern already in use). The `/api/setup/bootstrap` endpoint passes it explicitly.
- **`apps/cli/src/vela_cli/main.py`**: removes duplicated `_build_alembic_config` (uses `vela_core.migration.run_alembic_upgrade` instead). Keeps its existing `DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"`.
- **`packages/core/tests/test_bootstrap.py`**: removes duplicated `_run_alembic_upgrade` helper (uses `vela_core.migration.run_alembic_upgrade` instead). Tests already pass `script_location` explicitly.

## Capabilities

### New Capabilities
- `alembic-migration-runner`: Reusable Alembic config builder and migration runner isolated in a single core infrastructure module, eliminating triplicated `_build_alembic_config` logic.

### Modified Capabilities
- `local-setup-bootstrap`: The `run_local_setup_bootstrap` function's `script_location` parameter becomes required (no default). Callers — including the `/api/setup/bootstrap` endpoint — must pass it explicitly. The three-step orchestration behavior is unchanged.

## Impact

- **Breaking API change**: `run_local_setup_bootstrap(session, ..., script_location=...)` — `script_location` is now required. Affected callers: `apps/api/src/vela_api/main.py:142` (currently omits it), `packages/core/tests/test_bootstrap.py` (already passes it).
- **New module**: `packages/core/src/vela_core/migration.py` — the only module in core that imports `alembic`.
- **Deleted code**: `_build_alembic_config` in `bootstrap.py` and `apps/cli/main.py`; `ROOT`/`DEFAULT_ALEMBIC_SCRIPT_LOCATION` in `bootstrap.py`; `_run_alembic_upgrade` in `test_bootstrap.py`.
- **No spec behavior change**: all existing `local-setup-bootstrap` and `cli-database-initialization` scenarios remain valid — the three-step orchestration and CLI `init-db` behavior are unchanged.
- **No dependency changes**: `alembic` remains a project dependency; it is just no longer imported from `bootstrap.py`.

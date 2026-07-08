## 1. Create `vela_core/migration.py` module

- [x] 1.1 Create `packages/core/src/vela_core/migration.py` with `build_alembic_config(database_url: str, script_location: Path) -> Config` that constructs an `alembic.config.Config` with `script_location` and `sqlalchemy.url` set. This is the sole module in `vela_core` that imports `alembic`.
- [x] 1.2 Add `run_alembic_upgrade(database_url: str, script_location: Path) -> None` to the same module, which calls `command.upgrade(build_alembic_config(...), "head")`.
- [x] 1.3 Export `build_alembic_config` and `run_alembic_upgrade` from `packages/core/src/vela_core/__init__.py`.
- [x] 1.4 Add unit tests for `build_alembic_config` (asserts `script_location` and `sqlalchemy.url` are set on the returned `Config`) and `run_alembic_upgrade` (upgrades an empty SQLite DB to head, no-op on already-current DB).

## 2. Refactor `bootstrap.py` to use `migration.py`

- [x] 2.1 Remove `from alembic.config import Config` and `from alembic import command` from `packages/core/src/vela_core/bootstrap.py`.
- [x] 2.2 Remove `ROOT = Path(__file__).resolve().parents[4]` and `DEFAULT_ALEMBIC_SCRIPT_LOCATION` from `bootstrap.py`.
- [x] 2.3 Remove the `_build_alembic_config` helper function from `bootstrap.py`.
- [x] 2.4 Change `run_local_setup_bootstrap`'s `script_location` parameter from optional (with default) to **required** (no default value).
- [x] 2.5 Replace the step-1 migration call (`_build_alembic_config` + `command.upgrade`) with `run_alembic_upgrade(database_url, script_location)` imported from `vela_core.migration`.
- [x] 2.6 Add `from vela_core.migration import run_alembic_upgrade` to `bootstrap.py` imports.

## 3. Update API endpoint to pass `script_location`

- [x] 3.1 Add `DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"` to `apps/api/src/vela_api/config.py` (next to the existing `DEFAULT_STRATEGY_CONFIG_PATH`, reusing the existing `ROOT`).
- [x] 3.2 Import `DEFAULT_ALEMBIC_SCRIPT_LOCATION` in `apps/api/src/vela_api/main.py`.
- [x] 3.3 Update the `setup_bootstrap` endpoint (`main.py:142`) to pass `script_location=DEFAULT_ALEMBIC_SCRIPT_LOCATION` to `run_local_setup_bootstrap`.

## 4. Refactor CLI to use `migration.py`

- [x] 4.1 Remove `from alembic.config import Config` and `from alembic import command` from `apps/cli/src/vela_cli/main.py`.
- [x] 4.2 Remove the `_build_alembic_config` helper function from `apps/cli/src/vela_cli/main.py`.
- [x] 4.3 Update `init_db` to call `vela_core.migration.run_alembic_upgrade(database_url, script_location)` instead of building its own config.
- [x] 4.4 Keep the existing `DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"` in CLI (already present at `main.py:50`).

## 5. Update tests

- [x] 5.1 Remove the duplicated `_run_alembic_upgrade` helper from `packages/core/tests/test_bootstrap.py`; replace its usages with `vela_core.migration.run_alembic_upgrade`.
- [x] 5.2 Remove the duplicated `from alembic import command` and `from alembic.config import Config` imports from `test_bootstrap.py` (keep `Config` only if still needed for test-local assertions; prefer using `build_alembic_config` from `vela_core.migration`).
- [x] 5.3 Verify all existing `test_bootstrap.py` test cases still pass — they already pass `script_location=ALEMBIC_SCRIPT_LOCATION` explicitly, so no call-site changes needed.
- [x] 5.4 Add a test that `run_local_setup_bootstrap` raises `TypeError` when `script_location` is omitted (verifies the required-parameter contract).

## 6. Validate

- [x] 6.1 Run `ruff check .` — no new violations.
- [x] 6.2 Run `mypy packages/core/src apps/api/src apps/cli/src` — no new errors.
- [x] 6.3 Run the full test suite (`uv run pytest`) — all existing tests pass.
- [x] 6.4 Grep-confirm no remaining `from alembic import` or `import alembic` in `bootstrap.py` or `apps/cli/main.py` (only `vela_core/migration.py` and `alembic/env.py` should import alembic).
- [x] 6.5 Grep-confirm no remaining `parents[4]` in `packages/core/src/vela_core/bootstrap.py`.

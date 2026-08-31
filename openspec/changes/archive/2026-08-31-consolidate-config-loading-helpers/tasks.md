## 1. Characterize Existing Contracts

- [x] 1.1 Add focused tests for the Walk-forward raw base strategy loader covering a valid mapping, list/scalar/null documents, missing files, and malformed YAML; assert stable exception categories and non-mapping message markers without over-specifying dynamic parser/OS text.
- [x] 1.2 Add focused resolver tests for absolute paths, existing CWD-relative paths, strategy-directory fallback, and the collision case where both CWD and strategy-directory candidates exist; assert the current returned path form and CWD-first priority.

## 2. Consolidate Walk-forward Loading

- [x] 2.1 Implement the single raw mapping loader in `vela_core.walk_forward.config` using the existing UTF-8 `Path.open` and `yaml.safe_load` behavior, retaining native read/parser exceptions and the existing non-mapping `ValueError` semantics.
- [x] 2.2 Update `prepare_walk_forward_inputs()` and `WalkForwardRunner` to delegate to the shared loader, remove their duplicate `_load_base_config` implementations, and remove only now-unused direct YAML imports.

## 3. Consolidate Universe Path Resolution

- [x] 3.1 Promote the existing strategy resolver to module-public `resolve_universe_config_path()` without changing absolute, CWD-existing, strategy-directory fallback, or returned-path semantics.
- [x] 3.2 Update `load_strategy_config()` and `load_app_config()` to use the shared public resolver, remove the duplicate app-level private resolver, and confirm no caller imports a private cross-module helper.

## 4. Verify Behavior and Scope

- [x] 4.1 Run the focused configuration and Walk-forward regression tests, then run `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 4.2 Run `openspec validate consolidate-config-loading-helpers --strict` and `git diff --check`; verify the final diff contains only this Change's artifacts, required helper consolidation, caller cleanup, and tests, with no DB, Web, Linear, commit, or push actions.

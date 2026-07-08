## Context

`packages/core/src/vela_core/bootstrap.py` is the business orchestration module for local setup. It runs three steps in order: Alembic migrate → ETF pool sync → full market data fetch. Currently it directly imports `alembic.command` and `alembic.config.Config` (lines 6, 9) and computes the project root via `Path(__file__).resolve().parents[4]` (line 37) to locate the `alembic/` script directory.

The same `_build_alembic_config` + `command.upgrade` logic is copy-pasted in two other locations:
- `apps/cli/src/vela_cli/main.py:54-68` — CLI's `init_db` function
- `packages/core/tests/test_bootstrap.py:79-83` — test helper `_run_alembic_upgrade`

The project already uses the `ROOT = Path(__file__).resolve().parents[N]` pattern at the app layer for `DEFAULT_STRATEGY_CONFIG_PATH` (in both `apps/api/src/vela_api/config.py:6-7` and `apps/cli/src/vela_cli/main.py:49-51`).

## Goals / Non-Goals

**Goals:**
- Remove `import alembic` from `bootstrap.py` — the business orchestration module should not depend on a migration tool.
- Remove `parents[4]` path computation from `bootstrap.py` — core should not assume its position in the project directory tree.
- Eliminate the three copies of `_build_alembic_config` / `command.upgrade` — single source of truth.
- Keep the three-step bootstrap behavior and CLI `init-db` behavior identical (all existing specs pass unchanged).

**Non-Goals:**
- Fully removing `alembic` from `vela_core`'s dependency graph — the new `migration.py` module still imports it. Full decoupling (injecting a migration callable) was considered and rejected as over-engineering for a personal monorepo with a single migration implementation.
- Changing the `alembic/env.py` `sys.path` hack — that is Alembic's own entry point and is expected to know about the project structure.
- Making `script_location` configurable via environment variable or config file — `parents[N]` at the app layer is sufficient and consistent with the existing `DEFAULT_STRATEGY_CONFIG_PATH` pattern.

## Decisions

### Decision 1: Isolate alembic in a dedicated `migration.py` module (not inject a callable)

**Choice**: Create `packages/core/src/vela_core/migration.py` as the sole module that imports `alembic`. `bootstrap.py` imports `run_alembic_upgrade` from it.

**Alternatives considered**:
- **Inject `run_migrations: Callable[[], None]` into `run_local_setup_bootstrap`**: fully decouples core from alembic, but adds indirection with zero benefit — there is only one migration implementation in the project. Rejected as over-engineering.
- **Move alembic helpers to `apps/` shared code**: no natural home for app-level shared utilities in this monorepo; both apps already import from `vela_core`, so a core-level utility module is simpler.

**Rationale**: Isolating the import to one leaf module means `bootstrap.py` (business orchestration) is clean, while keeping the API simple (no callable injection). The dependency is contained, not eliminated — acceptable for an internal monorepo package.

### Decision 2: `script_location` becomes required (no default)

**Choice**: `run_local_setup_bootstrap(session, *, provider, app_config, database_url, script_location: Path)` — `script_location` is required.

**Rationale**: The current default (`parents[4] / "alembic"`) is the root cause of the fragility. Making it required forces callers to be explicit. The API endpoint (`apps/api/src/vela_api/main.py:142`) currently omits it — this is the most dangerous call site because it silently relies on the broken default. The tests already pass it explicitly, so they are unaffected.

### Decision 3: App layer uses `parents[N]` to compute `script_location`

**Choice**: Each app computes `DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"` using its existing `ROOT = Path(__file__).resolve().parents[N]`.

**Alternatives considered**:
- **Environment variable**: overkill for a personal local tool; requires a default fallback anyway.
- **Search for `pyproject.toml`**: self-adapting but adds filesystem traversal for no real benefit in a stable monorepo.
- **Parse `alembic.ini`**: circular — need to find `alembic.ini` first, which requires knowing the project root.

**Rationale**: The `parents[N]` pattern is already established for `DEFAULT_STRATEGY_CONFIG_PATH` in both apps. App-layer path computation is acceptable because apps are entry points — if the path breaks, it fails loudly at startup, not silently in a library. Core never computes paths; apps always do. This is the correct layer boundary.

### Decision 4: CLI's `init_db` calls `vela_core.migration.run_alembic_upgrade`

**Choice**: CLI removes its `_build_alembic_config` and calls the shared `run_alembic_upgrade` from `vela_core.migration`.

**Rationale**: Eliminates the duplication. CLI already imports extensively from `vela_core`, so no new dependency direction is introduced.

## Risks / Trade-offs

- **[Breaking API change for `run_local_setup_bootstrap` callers]** → Only one production call site (`apps/api/main.py`) omits `script_location`; tests already pass it. The migration is a one-line addition at the call site.
- **[Core still transitively depends on alembic via `migration.py`]** → Accepted. The goal is to isolate the dependency to one leaf module and remove it from business orchestration, not to eliminate it entirely. Full elimination would require callable injection, which adds complexity without consumers.
- **[App-layer `parents[N]` is still fragile]** → Accepted. App-layer fragility is qualitatively different from core-layer fragility: apps fail loudly at startup; core could fail silently when installed elsewhere. The `parents[N]` pattern is already used for `DEFAULT_STRATEGY_CONFIG_PATH` and has been stable.
- **[CLI's `init_db` signature gains a dependency on `vela_core.migration`]** → Not a new dependency direction; CLI already imports from `vela_core`.

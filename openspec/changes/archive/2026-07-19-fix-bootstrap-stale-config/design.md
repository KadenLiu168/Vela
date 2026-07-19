## Context

The FastAPI app (`apps/api/src/vela_api/main.py`) currently loads the strategy + ETF-pool config once at module-import time and stashes it on `app.state.strategy_config` (line 49). The `POST /api/setup/bootstrap` handler (line 158) passes that frozen copy into `run_local_setup_bootstrap`. This conflicts with every other config-consuming endpoint, which calls `load_app_config(...)` / `load_strategy_config(...)` fresh on each request.

Concretely, `run_local_setup_bootstrap` → `sync_etf_pool_to_db` persists `config/etf_pool.yaml` into `etf_info`. Because the bootstrap handler reads the startup-frozen copy, any edit to `etf_pool.yaml` made after the API started is silently ignored until the API process is restarted. This was verified end-to-end: editing `etf_pool.yaml` and clicking Bootstrap without restart writes the old ETF pool; restarting first makes the new pool take effect.

Grep confirms `app.state.strategy_config` has exactly two references in the application source — the assignment (line 49) and the read (line 158). Removing it is localized in code, but it also removes import-time config validation; that timing change is addressed explicitly below. The test suite has six additional references across three tests, which must switch to a live-read injection.

## Goals / Non-Goals

**Goals:**
- Make `POST /api/setup/bootstrap` read the current config from disk on each request, so config edits take effect without an API restart.
- Load one complete `AppConfig` before bootstrap orchestration starts and use that in-memory snapshot for the full request.
- Keep the response shape and the rest of the bootstrap orchestration unchanged.
- Align Bootstrap's config-loading behavior with `/api/config`, `/api/dashboard`, and `/api/strategy-signals/generate`.

**Non-Goals:**
- No change to `run_local_setup_bootstrap` or `sync_etf_pool_to_db` internals (they already accept `app_config` as a parameter).
- No schema/migration changes.
- No change to the `~1 minute` commit-after-fetch timing or the TablePlus non-auto-refresh behavior (unrelated, documented separately).
- No change to how other endpoints load config.

## Decisions

1. **Remove `app.state.strategy_config` entirely (line 49).**
   - Rationale: it is the sole source of the stale-config bug and has no other reader. Keeping a cached copy "for performance" is not worth the inconsistency — `load_app_config` is cheap (reads two small YAML files) and is already called per-request by other endpoints.
   - Consequence: the API module no longer loads config merely to initialize application state. Invalid config is therefore reported when a config-consuming endpoint is called, through the existing `ConfigError` handler, instead of preventing module import. This is consistent with the current behavior of `/api/config` and the strategy/backtest endpoints after startup.
   - Alternative considered: keep the cache but add a refresh hook on a POST `/api/config/reload`. Rejected — more surface area, more to test, and still inconsistent by default.
   - Alternative considered: retain the startup assignment only for fail-fast validation while Bootstrap ignores it. Rejected — it leaves an unused application-state object and performs duplicate I/O without preserving a usable application invariant.

2. **Bootstrap handler loads one request-scoped config before orchestration (line 158).**
   - Change `app_config=request.app.state.strategy_config` → `app_config=load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)`.
   - `load_app_config` and `DEFAULT_STRATEGY_CONFIG_PATH` are already imported in `main.py`, so no new imports are needed.
   - This makes Bootstrap behave consistently with the other endpoints: it performs a live per-request disk read (the other endpoints call `load_strategy_config(DEFAULT_STRATEGY_CONFIG_PATH)` or `load_app_config(...)` per request). Bootstrap specifically needs the full `AppConfig` (strategy + ETF pool), so it calls `load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)`.
   - The load happens exactly once before `run_local_setup_bootstrap`. The loaded models are detached from subsequent filesystem edits, so later file edits cannot change the config object already passed to the in-flight request.

3. **Update both affected specifications, not just the code.**
   - The `local-setup-bootstrap` spec currently expresses the frozen behavior as a scenario "Endpoint uses cached strategy config" under the requirement "HTTP endpoint for local setup bootstrap". The delta spec MODIFIES that requirement: removes the cached scenario and adds "Endpoint reads current strategy config from disk" (see specs delta), so the specification matches the corrected behavior. (Note: the cached behavior is a *scenario*, not a standalone requirement, so it must be removed via MODIFIED — not via a `## REMOVED Requirements` block naming a non-existent requirement, which would fail at archive.)
   - The `http-api-service` spec separately contains a standalone requirement "API caches loaded strategy config". The delta spec REMOVES that requirement because deleting `app.state.strategy_config` makes it false. Its claim that `/api/config` reuses the cached object is already inconsistent with `get_config_summary()`, which calls `load_app_config` per request.

4. **Test observable request behavior, not implementation wiring alone.**
   - Existing success and step-failure integration tests monkeypatch `vela_api.main.load_app_config` to keep their one-ETF fixture hermetic.
   - A focused endpoint test issues two requests while the loader returns two distinguishable `AppConfig` objects in sequence, then asserts `run_local_setup_bootstrap` receives the first and second objects respectively and the loader is called once per request with `DEFAULT_STRATEGY_CONFIG_PATH`. This proves there is no cross-request frozen copy without editing checked-in YAML or performing two full market-data fetches.
   - A failure-path test makes `load_app_config` raise `ConfigError`, asserts the stable HTTP 500 `config_error` envelope, and asserts `run_local_setup_bootstrap` is not called.

## Risks / Trade-offs

- [Risk] Three tests in `apps/api/tests/test_bootstrap_endpoint.py` inject config via `app.state.strategy_config`. After the fix that injection is a no-op, so the tests could silently bootstrap the real repo config and lose hermeticity. → Mitigation: monkeypatch `vela_api.main.load_app_config` in every bootstrap test that reaches orchestration.
- [Risk] Loading config per request surfaces file read, YAML parse, and validation failures as an HTTP 500 at Bootstrap time instead of at API import. → Mitigation: preserve the existing `ConfigError` envelope and verify that orchestration does not begin, so no partial bootstrap work occurs.
- [Trade-off] Bootstrap now re-reads disk each call; negligible cost for a manually-triggered, ~1-minute operation.
- [Trade-off] `load_app_config` reads the strategy YAML and the referenced ETF-pool YAML sequentially; it does not provide an atomic filesystem snapshot if an editor rewrites either file during those reads. This is acceptable for a local, manually triggered workflow. Each request still uses one validated in-memory `AppConfig` after loading; atomic multi-file config deployment is out of scope.
- [Pre-existing behavior] A changed pool does not delete ETF rows omitted from the YAML; `sync_etf_pool_to_db` only inserts or updates configured entries. The stale-config fix guarantees use of the new pool, not destructive reconciliation of removed entries.
- [Pre-existing risk] `_resolve_universe_config_path` first tests the configured relative path against the process working directory, then otherwise joins it to the strategy file's parent. With the checked-in value `config/etf_pool.yaml`, starting the API outside the repository root can resolve the wrong path. `scripts/dev.sh` is documented and run from the repository root, and path-resolution cleanup is unrelated to stale caching, so this change must not expand into that refactor.
- [Archival note] The baseline `http-api-service` Purpose currently mentions startup strategy-config caching. OpenSpec requirement deltas do not rewrite Purpose text, so the later archive step must remove that phrase when merging the removed cache requirement; this does not require an implementation change.

## Migration Plan

- Edit `main.py` (delete line 49, change line 158). Update the endpoint tests described in tasks 2.1–2.4. Run the focused endpoint/config tests plus `ruff` and `mypy`.
- No DB migration, no rollback data step. Rollback = revert the two-line change.

## Open Questions

- None blocking. Atomic reads across two YAML files and deletion of pool entries are explicitly out of scope.

## Why

Vela currently has duplicate implementations for Walk-forward base strategy raw YAML loading and universe config path resolution. This creates multiple authoritative implementations that can drift even though the current behavior is intentionally stable.

ECO-57 is the next low-risk core consolidation after the repository/dependency cleanup, and it removes those duplicate ownership points before the dependent ECO-58 runtime/session lifecycle work. The change is a behavior-preserving configuration helper consolidation: consolidate ownership, not semantics.

## What Changes

- Add one authoritative raw mapping loader in `vela_core.walk_forward.config` and make both `walk_forward/preflight.py` and `walk_forward/runner.py` delegate to it.
- Preserve the raw Walk-forward loader's existing read-error, YAML-parser, and non-mapping `ValueError` contracts and path-bearing error message semantics.
- Promote the existing strategy universe path resolver to the module-public `resolve_universe_config_path()` in `vela_core.strategy_config`.
- Make both `load_strategy_config()` and `load_app_config()` use that resolver, preserving absolute-path, CWD-existing, and strategy-directory fallback precedence and returned path form.
- Add focused characterization coverage for raw loader error categories and CWD-first priority when both relative candidates exist.
- Remove the duplicate private helpers and direct YAML imports from their callers where no longer needed.
- Do not add capabilities, redesign configuration loading, change schemas or models, alter API/CLI/DB/Web behavior, or implement ECO-58.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is an internal behavior-preserving refactor, so no living capability requirement changes.

This change declares `skip_specs: true`; no delta spec is created.

## Impact

Affected code is limited to the core configuration modules, their existing Walk-forward callers, and focused tests under the existing configuration/Walk-forward test layout. No new dependency, public root-package export, data model, persisted data, API, CLI, or Web surface is introduced.

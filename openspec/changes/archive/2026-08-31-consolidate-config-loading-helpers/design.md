## Context

See `proposal.md` for motivation. The two duplicated behaviors have different
contracts: the Walk-forward raw loader must retain native file/parser errors,
while typed configuration loading continues to use `ConfigError`. Universe
path lookup also has an existing CWD-first precedence that is part of the
compatibility boundary.

## Goals / Non-Goals

**Goals:**

- Make `vela_core.walk_forward.config` the sole owner of raw Walk-forward base strategy mapping loading.
- Make `vela_core.strategy_config.resolve_universe_config_path` the sole owner of universe path resolution.
- Preserve current exceptions, messages, path precedence, returned path form, and caller behavior.
- Prove the boundaries with focused characterization tests.

**Non-Goals:**

- No generic YAML/path abstraction, configurable error policy, schema/model change, or root-package re-export.
- No changes to typed loader `ConfigError` behavior, Walk-forward orchestration, API, CLI, DB, or Web.

## Decisions

1. **Keep the raw loader in `walk_forward.config`.** Add one small function that opens the file with UTF-8, calls `yaml.safe_load`, checks for `dict`, and raises the existing `ValueError` for non-mapping documents. This is preferred over reusing `vela_core.config._load_yaml()` because wrapping errors would change the established contract. A generic raw-YAML API or error-policy switch would add a wider abstraction for one use case.

2. **Expose the existing universe resolver from `strategy_config`.** Rename the private helper to `resolve_universe_config_path` and have both strategy and app loaders call it. This keeps strategy-owned field semantics local; a new generic resolver module would create an abstraction without another consumer.

3. **Test behavior at the helper boundary and retain existing regressions.** Add direct tests for valid/non-mapping/missing/malformed raw YAML and all resolver precedence cases, including the CWD-versus-strategy-directory collision. Existing configuration and Walk-forward suites remain unchanged except for necessary imports or focused additions.

## Risks / Trade-offs

- [Risk] A future caller may expect raw loading to use `ConfigError` → Mitigation: document and test that the raw Walk-forward helper intentionally preserves its native exception contract.
- [Risk] A resolver refactor could silently change relative path precedence → Mitigation: explicit tests cover absolute, CWD-existing, fallback, and collision cases.
- [Risk] Duplicate imports or private references remain after delegation → Mitigation: targeted search and the full Python gate catch stale references and type/lint issues.

## Context

See `proposal.md` for motivation. The complete local checkout confirms no active Python source or tests directly import `numpy`, `pydantic_settings`, or `pytest_cov`; pytest configuration and GitHub CI contain no coverage options. Configuration uses Pydantic `BaseModel` objects populated by YAML loaders, while historical OpenSpec material, generated metadata, and cached analysis files contain non-operational references that do not establish a direct dependency.

The change must preserve the current environment rather than require removed packages to vanish transitively. In particular, pandas and other retained dependencies may continue to resolve NumPy.

## Goals / Non-Goals

**Goals:**

- Make Vela's direct Python dependency declarations match active direct usage.
- Keep lockfile generation reproducible through `uv` and prove the existing Python gate still passes.
- Preserve configuration and test behavior without executable-source changes.

**Non-Goals:**

- Prune other dependencies, generated metadata, historical documents, or transitive packages.
- Consolidate configuration helpers or introduce replacement settings or numerical abstractions.
- Add or redesign coverage policy, pytest behavior, packaging, or CI.

## Decisions

### Remove declarations without rewriting callers

Delete only the three named entries from `pyproject.toml`. No source or test edits are planned because the local direct-import and tooling scan found no callers to migrate. Rewriting code to manufacture removability was rejected because it would turn metadata cleanup into a behavior change.

### Treat direct dependency state as the acceptance boundary

Acceptance checks Vela's declarations and direct imports, not package-name absence from `uv.lock`. A package legitimately retained through another declared dependency remains valid; relying on such transitive installation from Vela code does not. Requiring complete lockfile absence was rejected because it would incorrectly force changes to retained dependencies such as pandas.

### Regenerate generated state only through `uv`

After editing `pyproject.toml`, run `uv lock` and then `uv sync --group dev`; do not manually edit `uv.lock`. Inspect the resulting diff to reject unrelated dependency upgrades or pruning beyond resolver output attributable to the three removals.

### Keep documentation correction surgical

Remove `pydantic-settings` only from the root README backend Tech Stack line. Historical OpenSpec records, generated `*.egg-info`, cached analysis output, and unrelated documentation are not authoritative dependency declarations and remain untouched.

### Use existing tests as behavior evidence

Do not add deletion-specific unit tests. The full Python CI-equivalent gate exercises the supported application and configuration behavior after dependency resolution; a Web gate is unnecessary because no Web surface changes.

## Risks / Trade-offs

- A missed dynamic or tooling-only dependency could fail after removal → repeat exact-name/import/coverage-option scans across active source, tests, scripts, configuration, CI, and tooling before editing, then run `uv sync` and the full Python gate.
- Resolver output may retain NumPy transitively → verify the root Vela package no longer declares it and that active Vela code has no direct NumPy import; do not treat transitive retention as failure.
- `uv lock` could produce unrelated churn → inspect the lockfile diff and stop rather than accepting unrelated upgrades or hand-editing generated state.
- Removing `pydantic-settings` could be mistaken for configuration redesign → require no executable configuration changes and rely on the existing configuration tests within the full Python gate.

## Migration Plan

1. Reconfirm the three no-direct-use facts against active operational files.
2. Remove the three declarations and update only the affected README wording.
3. Regenerate and synchronize dependency state with `uv`.
4. Run the full Python CI-equivalent gate and inspect the final scoped diff.

If validation exposes a real direct requirement, stop and restore the dependency metadata through the same `pyproject.toml` plus `uv` workflow; do not alter business behavior to force removal.

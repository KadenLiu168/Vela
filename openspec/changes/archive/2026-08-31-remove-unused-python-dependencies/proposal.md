## Why

Vela directly declares `numpy`, `pydantic-settings`, and `pytest-cov` even though the active local checkout does not directly import or require them. With ECO-55 complete, removing these stale declarations now keeps the dependency contract aligned with the implementation before ECO-57 changes configuration helpers.

## What Changes

- Remove `numpy` and `pydantic-settings` from `[project].dependencies`.
- Remove `pytest-cov` from the dev dependency group without adding a coverage gate or threshold.
- Regenerate `uv.lock` through the normal `uv` workflow; packages still required transitively may remain in the resolved lockfile.
- Remove only `pydantic-settings` from the root README backend Tech Stack wording.
- Preserve runtime behavior, configuration semantics, public API and CLI contracts, tests, data models, database behavior, and existing quality-gate definitions.

## Capabilities

### New Capabilities

None. This is repository/dependency-state cleanup and introduces no product behavior.

### Modified Capabilities

None. Existing capability requirements remain unchanged, so this change opts out of delta specs with `skip_specs: true`.

## Impact

Implementation is limited to `pyproject.toml`, the `uv`-generated `uv.lock`, and the affected root `README.md` Tech Stack line. No executable source, tests, Web files, database state, archived OpenSpec material, or ECO-57 configuration work is expected to change.

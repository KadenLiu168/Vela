## Context

See `proposal.md` for motivation. The three removal groups are spread across separate core modules but share the same implementation property: current repository-wide reference tracing finds no production consumer. The existing living specifications require the surviving `forward_adjusted_prices()` behavior, `ResolvedSessionPrice` semantics, target-weight equity-curve behavior, and versioned Walk-forward evidence models; none requires the candidate symbols.

The Change must remain deletion-only, preserve the repository-root `vela.db`, and avoid converting internal cleanup into a new compatibility or abstraction layer.

## Goals / Non-Goals

**Goals:**

- Remove only symbols proven unreachable from current production and test callers, plus the one test that exists solely for an unused projection.
- Preserve the canonical implementations and versioned contracts that replaced those symbols.
- Leave imports, formatting, typing, and tests clean after the deletions.
- Produce verification evidence sufficient to distinguish dead-code removal from a behavior change.

**Non-Goals:**

- Refactoring adjusted-price calculation, resolved-session construction, target-weight allocation/rebalancing, or Walk-forward evidence validation.
- Renaming or consolidating surviving versioned evidence models or report `TypedDict` types.
- Changing API, CLI, persistence, database, dependency, or Web behavior.
- Adding compatibility shims, deprecation aliases, new abstractions, or delta specs.

## Decisions

### 1. Delete the unused projection instead of redirecting it

Remove `ResolvedAdjustedPrice` and `resolved_adjusted_prices()` and delete only their dedicated test and import. Production consumers already operate on `ResolvedSessionPrice` or use `forward_adjusted_prices()` directly, so redirecting the unused function would retain an unnecessary representation and imply a supported surface.

Alternative considered: keep the function as a compatibility wrapper. Rejected because it is not exported, has no active caller, and no specification requires it.

### 2. Remove wrapper functions without changing their surviving callees

Delete `_allocate_target()` and `_rebalance()` while leaving `_allocate_target_weights()`, `_rebalance_target()`, and `_normalized_target_weights()` unchanged. This makes the change mechanically reviewable and avoids conflating dead wrapper removal with equity-curve behavior changes.

Alternative considered: rename or reorganize the surviving helpers. Rejected as unrelated refactoring.

### 3. Keep versioned evidence names explicit

Delete `SUPPORTED_EVIDENCE_VERSIONS` and the six unversioned aliases at the bottom of `walk_forward/evidence.py`. Retain `EVIDENCE_VERSION`, `EVIDENCE_VERSION_V2`, `EVIDENCE_VERSION_V3`, the corresponding versioned models, `validate_wf_evidence()`, and the independent same-named `TypedDict` definitions in `walk_forward/report.py`.

Alternative considered: replace the tuple or aliases with a registry. Rejected because there is no caller requiring a registry and the existing explicit version dispatch remains authoritative.

### 4. Verify reachability before and after deletion

Apply must repeat repository-wide exact-symbol searches before editing, then prove the removed names have no remaining references. It must run focused tests for adjusted-price projection, strategy equity curves, and Walk-forward evidence/report behavior before the complete Python CI-equivalent gate. Tests that write data must continue to use their own temporary databases; no real application command or repository database is needed.

## Risks / Trade-offs

- [An untracked or dynamically imported consumer depends on a removed name] → Search tracked source, tests, application entrypoints, and string references; then use mypy and the complete test suite as independent import/call-chain checks.
- [Removing the projection test loses required resolved-session coverage] → Remove only assertions specific to `resolved_adjusted_prices()` and retain the existing forward-adjusted and resolved-session contract suites.
- [Same-spelled report types are mistaken for the aliases being deleted] → Limit edits to assignments in `walk_forward/evidence.py`; do not change `walk_forward/report.py` types.
- [Cleanup expands into adjacent refactoring] → Enforce the proposal's four-file implementation allowlist and inspect the final diff before completion.

## Migration Plan

No data, schema, configuration, or compatibility migration is required. Apply the deletions, run focused and full verification, and roll back by reverting only the scoped source/test edits if an unexpected consumer is found.

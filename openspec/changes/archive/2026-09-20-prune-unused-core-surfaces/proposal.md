## Why

Three internal core surfaces remain after their production callers moved to `ResolvedSessionPrice`, target-weight helpers, and explicitly versioned Walk-forward evidence models. They now have no runtime consumers, while one test-only projection and several compatibility-looking names create misleading maintenance and API surface.

## What Changes

- Remove `ResolvedAdjustedPrice` and `resolved_adjusted_prices()`, together with the import and test that exercise only that unused projection.
- Remove the uncalled `_allocate_target()` and `_rebalance()` wrappers while retaining the target-weight implementations used by production code.
- Remove `SUPPORTED_EVIDENCE_VERSIONS` and the six unused unversioned Walk-forward evidence aliases while retaining all version constants, versioned evidence models, validators, and report-owned `TypedDict` types.
- Verify that the removals leave no active references and preserve all externally observable pricing, equity-curve, Walk-forward evidence, API, CLI, persistence, and database behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is an internal dead-code removal with no requirement-level behavior change, so the Change sets `skip_specs: true`.

## Impact

- Affected implementation: `packages/core/src/vela_core/adjusted_price_projection.py`, `packages/core/src/vela_core/strategy_equity_curve.py`, and `packages/core/src/vela_core/walk_forward/evidence.py`.
- Affected tests: `packages/core/tests/test_adjusted_price_projection.py` only, limited to removing the test-only projection coverage and its now-unused imports.
- Unchanged: living specs, public application behavior, versioned evidence parsing, database schema/data, dependencies, API and CLI contracts, Web code, and persisted `vela.db`.
- Validation requires focused reference/test checks followed by the repository's complete Python gate, strict OpenSpec validation, and diff/scope inspection.

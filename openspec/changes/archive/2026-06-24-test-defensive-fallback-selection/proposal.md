## Why

COP-71 requires explicit test coverage for defensive asset fallback selection. The fallback behavior already exists in the momentum scoring contract, but the no-ranked-candidates trigger boundary should be made explicit and verified.

## What Changes

- Add focused unit coverage for defensive fallback selection when ranked ETF candidates are unavailable.
- Keep existing non-fallback behavior verified when ranked ETF candidates satisfy `selection.top_n`.
- Do not change production selection behavior, database schema, CLI behavior, or configuration semantics.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `momentum-scoring`: Clarify that defensive fallback applies when no ranked ETF candidates are available, and verify the defensive asset and full target weight output.

## Impact

- Affected tests: `packages/core/tests/test_momentum_scoring.py`
- Affected specs: `openspec/specs/momentum-scoring/spec.md`
- No API, dependency, schema, or runtime behavior changes.

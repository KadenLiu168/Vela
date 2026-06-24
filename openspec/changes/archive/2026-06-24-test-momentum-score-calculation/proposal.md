## Why

COP-69 needs explicit test coverage proving momentum score calculation stays correct across configured momentum windows and score weight combinations. The existing scoring API is already present, but regression coverage should make the weighted formula and reproducibility contract harder to break.

## What Changes

- Add focused core tests for multiple configured short/long momentum windows and score weight combinations.
- Verify each score is reproducible for identical database rows and strategy configuration.
- Keep the production momentum scoring API unchanged unless the new tests expose a defect.

## Capabilities

### New Capabilities

### Modified Capabilities
- `momentum-scoring`: Clarify coverage of multiple valid configured window and score weight combinations for weighted momentum score calculation.

## Impact

- Affected code: `packages/core/src/vela_core/momentum_scoring.py` only if tests expose a necessary fix.
- Affected tests: `packages/core/tests/test_momentum_scoring.py`.
- Dependencies: no new runtime dependencies.
- Systems: Phase 1 core backend strategy scoring confidence for signal generation and backtesting.

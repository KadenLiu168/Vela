## Why

Strategy signal generation needs a deterministic fallback when momentum-ranked ETF candidates cannot satisfy the configured Top N selection. COP-51 requires switching to the configured defensive asset in that case so downstream signal generation can always express a defensive position instead of an undersized risky allocation.

## What Changes

- Add defensive fallback selection behavior for ranked momentum results.
- Trigger fallback when the number of ranked ETF candidates is less than `selection.top_n`.
- Return the configured defensive asset identity with full target weight when fallback triggers.
- Preserve existing Top N behavior when enough ranked candidates are available.
- Add unit tests covering fallback-triggered and fallback-not-triggered scenarios.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `momentum-scoring`: Extend ETF selection requirements to apply the configured defensive asset fallback when ranked candidates do not satisfy Top N.

## Impact

- `packages/core/src/vela_core/momentum_scoring.py`
- `packages/core/src/vela_core/__init__.py`
- `packages/core/tests/test_momentum_scoring.py`
- `openspec/specs/momentum-scoring/spec.md`

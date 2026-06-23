## Why

ETF rotation signal generation needs an explicit Top N selection step after momentum ranking. The current ranking helper can be sliced by callers, but it does not define target weights or the behavior when fewer eligible ETFs exist than the configured Top N.

## What Changes

- Add a Top N ETF selection result that includes ETF id, rank, score, and target weight.
- Add a pure selection helper that uses `StrategyConfig.selection.top_n`.
- Select the highest-ranked eligible ETFs from existing `MomentumRanking` values.
- Define insufficient-eligible behavior: return all available ranked ETFs and assign target weights across the actual selection count.
- Do not change scoring, ranking order, trend filtering, persistence models, database schema, CLI behavior, or defensive-asset fallback.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `momentum-scoring`: Add explicit Top N ETF selection behavior and target-weight output after momentum ranking.

## Impact

- Core package: adds a small selection result type and pure helper near existing momentum scoring code.
- Public exports: exposes the selection type and helper from `vela_core`.
- Tests: adds focused unit tests for configured Top N, insufficient eligible ETFs, empty selections, and target weights.
- Specs: updates the existing `momentum-scoring` capability.

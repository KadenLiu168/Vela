## Why

Strategy signal generation needs a reproducible way to rank ETF candidates from configured momentum inputs. Vela already validates strategy momentum windows and score weights, and it can calculate price-window returns, but it does not yet expose a tested weighted momentum score that combines those pieces.

## What Changes

- Add a core weighted momentum score calculation for one ETF at an `as_of_date`.
- Use `strategy_v1.yaml`-style configuration for the short and long momentum windows and their score weights.
- Return the component short and long returns together with the combined score for diagnostics and later ranking.
- Define missing-data behavior explicitly: if either configured window return is unavailable, the combined score is unavailable.
- Add focused unit tests for typical inputs, configured windows, reproducibility, and missing history.

## Capabilities

### New Capabilities
- `momentum-scoring`: Calculates configured short/long momentum returns and combines them into a weighted momentum score.

### Modified Capabilities

## Impact

- Affected code: `packages/core/src/vela_core/` scoring module and package exports.
- Affected tests: new focused core tests for weighted momentum scoring.
- Dependencies: no new runtime dependencies.
- Systems: prepares signal generation and backtesting to consume reproducible ETF momentum scores.

## Why

ETF rotation signal generation needs a stable way to order candidates after weighted momentum scores are calculated. Without an explicit ranking contract, Top N selection can become ambiguous when scores tie or when some ETFs lack enough market data to produce a score.

## What Changes

- Add deterministic ETF ranking behavior for already-calculated momentum scores.
- Exclude ETFs whose weighted momentum score is missing from ranked results.
- Sort ranked ETFs by score descending, with a stable tie-breaker.
- Produce continuous 1-based ranks that callers can use directly for Top N selection.
- Do not change the momentum score formula, trend filter, database schema, CLI, or signal persistence models.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `momentum-scoring`: Add requirements for deterministic ranking of ETF momentum scores and Top N usability.

## Impact

- Core package: adds a small ranking result type and pure ranking function near existing momentum scoring code.
- Public exports: exposes the ranking type and function from `vela_core`.
- Tests: adds focused unit tests for ordering, ties, missing scores, rank assignment, and Top N slicing.
- Specs: updates the existing `momentum-scoring` capability with ranking behavior.

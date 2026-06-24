## Context

`calculate_momentum_score` already calculates configured short and long returns from `MarketPrice.strategy_price` and combines them with `StrategyConfig.score_weights`. Existing tests cover typical scoring, configured windows, reproducibility, missing data, and ETF isolation, but COP-69 asks specifically for testing multi-window returns and weight combinations.

## Goals / Non-Goals

**Goals:**
- Add focused test coverage for multiple configured short/long window lengths and score weight combinations.
- Verify each covered combination returns deterministic component returns and weighted score values.
- Keep the change limited to core momentum scoring tests unless a defect is exposed.

**Non-Goals:**
- Do not change momentum scoring API shape.
- Do not change ranking, Top N selection, defensive fallback, signal generation, or backtesting behavior.
- Do not introduce new configuration options or dependencies.

## Decisions

1. Use parametrized pytest cases for window and weight combinations.

   Rationale: parametrization keeps the test compact while making each combination explicit in pytest output.

   Alternative considered: separate tests per combination. That is easier to read in isolation but repeats the same setup and increases maintenance without adding coverage.

2. Assert complete result objects for reproducibility-sensitive cases.

   Rationale: asserting `MomentumScore` values checks `etf_id`, `as_of_date`, component returns, and weighted score together, so regressions in result shape or deterministic output are visible.

   Alternative considered: assert only the final score. That would miss component-return regressions that happen to offset in the weighted result.

## Risks / Trade-offs

- Decimal expected values can be brittle if written from float arithmetic -> Use exact `Decimal` literals derived from simple price ratios and validated score weights.
- Parametrized setup can obscure row-window indexing -> Keep fixture data tied to explicit offsets matching the configured windows in each case.

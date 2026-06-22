## Context

Vela already has a checked-in `config/strategy_v1.yaml`, a Pydantic schema in the core package, and tests for required strategy parameter groups. Current validation rejects non-positive momentum windows and score weights whose total is not 1.0, but it still allows ambiguous calculation inputs such as equal short/long windows or a zero weight for one momentum component.

## Goals / Non-Goals

**Goals:**

- Strengthen the existing strategy configuration schema so invalid momentum window relationships are rejected before strategy calculation.
- Make score weight legality explicit by requiring both configured momentum components to have positive weight and a normalized total.
- Add focused tests for the newly rejected invalid configurations.

**Non-Goals:**

- Implement momentum calculation, signal generation, rebalancing, or backtesting logic.
- Change the `config/strategy_v1.yaml` file shape or introduce a new config version.
- Add a generic strategy DSL or configurable number of scoring windows.
- Validate cross-file consistency between the defensive asset and ETF universe.

## Decisions

1. Keep validation inside the existing Pydantic models.

   Rationale: `MomentumConfig` and `ScoreWeightsConfig` already own field-level strategy parameter validation. Adding narrow validators there keeps the public loader and YAML shape unchanged.

   Alternative considered: add a separate strategy validation function after model parsing. That would split one config contract across two places without a current need.

2. Require `short_window_days < long_window_days`.

   Rationale: The v1 config names these windows as short and long, and future dual momentum scoring expects distinct horizons ordered by length. Equal or reversed windows make the two score components redundant or misleading.

   Alternative considered: only require positive values. That preserves current behavior but does not satisfy the stronger calculation-readiness requirement.

3. Require each score weight to be positive and keep total normalization.

   Rationale: The v1 scoring contract contains exactly two momentum components. A zero component would silently disable one configured signal while still looking like a dual-window score.

   Alternative considered: allow zero weights as long as the total is 1.0. That is more flexible, but flexibility is not needed for the current fixed v1 strategy contract.

## Risks / Trade-offs

- Existing local custom configs with a zero score weight will become invalid -> Keep the checked-in config unchanged and cover the new behavior with explicit tests.
- Floating point totals can be noisy -> Preserve the existing tolerance for the total weight check.
- Future strategies may want single-window scoring -> Introduce a new config version or schema change when that requirement exists instead of weakening v1 validation now.

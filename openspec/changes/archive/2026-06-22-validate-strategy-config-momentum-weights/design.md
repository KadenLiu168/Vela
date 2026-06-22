## Context

Vela already has a checked-in `config/strategy_v1.yaml`, a Pydantic strategy schema, an ETF pool schema, and tests for required strategy parameter groups. Current validation rejects non-positive momentum windows and unnormalized score weights, but strategy calculation also relies on ordered momentum windows, positive contribution from each configured score component, and a defensive fallback asset that can actually be traded from the configured ETF universe.

## Goals / Non-Goals

**Goals:**

- Strengthen the existing strategy configuration schema so invalid momentum window relationships are rejected before strategy calculation.
- Make score weight legality explicit by requiring both configured momentum components to have positive weight and a normalized total.
- Validate that `defense.asset` exists in the `universe_config` ETF pool and is active.
- Add focused tests for the newly rejected invalid configurations.

**Non-Goals:**

- Implement momentum calculation, signal generation, rebalancing, or backtesting logic.
- Change the `config/strategy_v1.yaml` file shape or introduce a new config version.
- Add a generic strategy DSL, configurable number of scoring windows, or defensive asset allowlist.
- Add database-backed ETF universe lookup.

## Decisions

1. Keep single-file strategy validation inside the existing Pydantic models.

   Rationale: `MomentumConfig` and `ScoreWeightsConfig` already own field-level strategy parameter validation. Adding narrow validators there keeps the public loader and YAML shape unchanged.

   Alternative considered: add a separate strategy validation function after model parsing. That would split one config contract across two places without a current need.

2. Require `short_window_days < long_window_days`.

   Rationale: The v1 config names these windows as short and long, and future dual momentum scoring expects distinct horizons ordered by length. Equal or reversed windows make the two score components redundant or misleading.

   Alternative considered: only require positive values. That preserves current behavior but does not satisfy the stronger calculation-readiness requirement.

3. Require each score weight to be positive and keep total normalization.

   Rationale: The v1 scoring contract contains exactly two momentum components. A zero component would silently disable one configured signal while still looking like a dual-window score.

   Alternative considered: allow zero weights as long as the total is 1.0. That is more flexible, but flexibility is not needed for the current fixed v1 strategy contract.

4. Validate defensive asset tradability in `load_strategy_config()`.

   Rationale: `StrategyConfig.model_validate(...)` can validate only the strategy file shape, while fallback tradability depends on loading the ETF pool referenced by `universe_config`. The loader is the existing boundary that can safely combine these files and still return the same `StrategyConfig` type.

   Alternative considered: add a new public validation function. That would preserve current loader behavior, but it would be easy for callers to accidentally skip the cross-file safety check.

## Risks / Trade-offs

- Existing local custom configs with zero score weight or inactive fallback assets become invalid -> Keep the checked-in config unchanged and cover the stricter behavior with explicit tests.
- Relative `universe_config` paths can be ambiguous -> Resolve paths relative to the current working directory first to preserve the checked-in config, then relative to the strategy config file for test/local config ergonomics.
- Future strategies may want single-window scoring or out-of-universe defensive instruments -> Introduce a new config version or explicit allowlist only when that requirement exists.

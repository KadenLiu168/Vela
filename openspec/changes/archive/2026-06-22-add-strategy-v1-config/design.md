## Context

Vela currently has ETF metadata, market price storage, signal run persistence, and backtest run persistence, but no checked-in strategy parameter contract. The repository has `config/etf_pool.yaml` for the Phase 1 ETF universe and includes Pydantic as a dependency, but no strategy configuration schema or loader exists yet.

This change establishes the first strategy configuration contract without implementing the strategy calculation itself.

## Goals / Non-Goals

**Goals:**

- Define a minimal `config/strategy_v1.yaml` for a versioned ETF rotation strategy.
- Validate the config with a small Pydantic schema in the core package.
- Include the strategy parameters needed by future signal and backtest code: momentum windows, score weights, Top N selection, defensive asset, and transaction costs.
- Keep tests focused on validation behavior and the checked-in YAML file.

**Non-Goals:**

- Implement momentum calculation, signal generation, rebalancing, or backtesting behavior.
- Add database tables or migrations.
- Add CLI commands or API endpoints for strategy config management.
- Support multiple config formats or dynamic remote config sources.

## Decisions

1. Store the initial strategy config as YAML at `config/strategy_v1.yaml`.

   Rationale: The project already uses YAML for `config/etf_pool.yaml`, and a checked-in file is enough for Phase 1 reproducibility.

   Alternative considered: store strategy parameters in Python constants. That would be simpler to load but weaker as a user-editable, versioned configuration artifact.

2. Add schema and loading behavior to `packages/core/src/vela_core`.

   Rationale: Strategy signals and backtests will both depend on the same validated configuration, so the contract belongs in the shared core package instead of the CLI app.

   Alternative considered: put validation in `apps/cli`. That would couple validation to one entrypoint and make future API/backtest usage duplicate config parsing.

3. Keep the schema narrow and explicit.

   Rationale: Phase 1 needs enough validation to protect known strategy parameters, not a generic strategy DSL. The schema should validate required fields, positive window lengths, positive `top_n`, normalized weights, and non-negative transaction costs.

   Alternative considered: create a flexible nested parameter map. That would avoid schema changes later but would not satisfy the goal of Pydantic validation for the initial contract.

4. Model the defensive asset as an exchange/symbol pair.

   Rationale: ETF metadata already treats ETF identity as exchange plus symbol, and `config/etf_pool.yaml` follows the same shape. This avoids treating symbols as globally unique.

   Alternative considered: use only a symbol string. That is shorter but ambiguous across exchanges.

## Risks / Trade-offs

- The first schema may need changes when strategy logic becomes concrete -> Keep this config versioned as `v1` and preserve future changes as new versions or explicit schema migrations.
- Weight validation can be too strict with floating point values -> Use a small tolerance for checking total score weight.
- A checked-in defensive asset may not exist in a loaded ETF universe -> Validate shape now and leave cross-file universe consistency to either this change if simple or a later loader integration if it would add unnecessary complexity.
- YAML parsing adds a dependency question -> Prefer an already available YAML parser if present in the environment; otherwise add the smallest appropriate dependency only if required by implementation.

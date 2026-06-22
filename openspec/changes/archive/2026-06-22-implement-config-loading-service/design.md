## Context

Vela currently has `ETFPoolConfig` plus `load_etf_pool_config()` in `vela_core.config`, and `StrategyConfig` plus `load_strategy_config()` in `vela_core.strategy_config`. The checked-in `config/strategy_v1.yaml` references `config/etf_pool.yaml` through `universe_config`, but there is no single public service that loads both files and returns the complete typed configuration needed by strategy generation or backtesting.

## Goals / Non-Goals

**Goals:**

- Provide one core-level loading entrypoint for the strategy configuration and referenced ETF pool.
- Return a typed aggregate object so callers do not pass loosely typed dictionaries between workflows.
- Reuse existing YAML parsing, Pydantic validation, and `ConfigError` reporting.
- Keep path resolution deterministic for the checked-in config and local test configs.

**Non-Goals:**

- Change the shape of `config/strategy_v1.yaml` or `config/etf_pool.yaml`.
- Add a CLI command, database persistence, environment-variable loading, or settings framework.
- Implement strategy signal generation or backtesting behavior.
- Introduce a generic multi-strategy plugin or config registry.

## Decisions

1. Add a small typed aggregate model, tentatively `AppConfig`, with `strategy: StrategyConfig` and `etf_pool: ETFPoolConfig`.

   Rationale: A named aggregate is clearer than returning a tuple and keeps future workflow signatures explicit.

   Alternative considered: return `(StrategyConfig, ETFPoolConfig)`. That is smaller, but it loses field names and makes call sites easier to mix up.

2. Use the strategy config path as the service entrypoint.

   Rationale: `StrategyConfig.universe_config` already defines which ETF pool belongs to a strategy. Making callers pass two independent paths can create conflicting configuration state.

   Alternative considered: require both paths. That is more direct for tests, but it bypasses the existing strategy-to-universe relationship.

3. Resolve relative `universe_config` paths from the current working directory first, then from the strategy config file directory.

   Rationale: The checked-in `config/strategy_v1.yaml` uses `config/etf_pool.yaml`, which works from the repository root. Falling back to the strategy file directory keeps temporary test configs ergonomic without changing the checked-in file.

   Alternative considered: resolve only relative to the strategy config file. That is common for nested config bundles, but it would make the existing repository-root-relative value point at `config/config/etf_pool.yaml`.

4. Reuse `ConfigError` instead of adding a new service-specific exception.

   Rationale: The existing application-configuration spec already defines project-level config error reporting for read, parse, and validation failures.

   Alternative considered: introduce `ConfigServiceError`. That adds another exception type without a separate failure category.

## Risks / Trade-offs

- Active OpenSpec change overlap with defensive asset validation -> Keep this service focused on loading both typed configs and let implementation reuse whichever defensive-asset validation lands first.
- Current-working-directory path resolution can depend on how tests or apps are launched -> Use an explicit fallback order and cover it with tests.
- Future workflows may need explicit ETF pool overrides -> Add a separate override API later only when a real caller needs it.

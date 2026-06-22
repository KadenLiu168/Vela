## Why

The previous configuration change introduced a generic `StrategyEnvelopeConfig`, but Vela already has the formal `strategy-configuration` capability and `StrategyConfig` model for `config/strategy_v1.yaml`. Keeping both creates two competing strategy configuration concepts and increases the chance of bypassing the strict v1 strategy schema.

## What Changes

- Remove the strategy envelope configuration concept from application configuration.
- Keep application configuration focused on ETF pool YAML schemas, typed ETF pool loading, and shared `ConfigError` behavior.
- Route strategy configuration loading through the existing `StrategyConfig` model.
- Wrap `load_strategy_config()` file read, YAML parse, and Pydantic validation failures in `ConfigError`.
- Update tests to cover ETF pool config and concrete strategy config loader errors.

## Capabilities

### New Capabilities

No new capabilities.

### Modified Capabilities

The existing `application-configuration` capability is narrowed by removing strategy envelope requirements and clarifying the capability purpose.

The existing `strategy-configuration` capability gains clear loader error behavior for strategy configuration files.

## Impact

- Affects `packages/core` configuration modules and public exports.
- Affects focused core tests for configuration loading failures.
- Affects OpenSpec main specs for application and strategy configuration.
- Does not rewrite or edit archived historical changes.

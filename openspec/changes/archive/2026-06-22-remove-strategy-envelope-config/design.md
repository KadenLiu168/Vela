## Context

Vela now has two strategy configuration concepts: the concrete `StrategyConfig` for `config/strategy_v1.yaml`, and the generic `StrategyEnvelopeConfig` added under application configuration. The concrete strategy configuration is the active contract for Phase 1 strategy signal and backtesting work.

## Goals / Non-Goals

**Goals:**

- Remove the unused strategy envelope model and loader.
- Keep ETF pool configuration under application configuration.
- Keep concrete strategy parameters under strategy configuration.
- Reuse `ConfigError` for strategy config loader failures.
- Preserve the existing archived change as historical record.

**Non-Goals:**

- Do not rewrite git history or amend the previous pushed commit.
- Do not edit the archived `define-pydantic-config-schema` change.
- Do not change the concrete `config/strategy_v1.yaml` schema.

## Decisions

### Remove StrategyEnvelopeConfig

`StrategyEnvelopeConfig` is not used by business code and overlaps with the existing `StrategyConfig`. Removing it prevents developers from choosing the wrong strategy configuration entrypoint.

Alternative considered: keep it but stop exporting it. That still leaves an unused strategy abstraction in the codebase and specs.

### Keep ConfigError in application configuration

`ConfigError` remains the shared loader error type because it is useful for both ETF pool and strategy file loading. Strategy-specific validation remains in `strategy_config.py`.

Alternative considered: duplicate a strategy-specific error type. That adds no current value and makes CLI-facing error handling less consistent.

### Wrap existing strategy loader failures

`load_strategy_config()` should continue returning `StrategyConfig`, but it should convert file read, YAML parse, and Pydantic validation failures into `ConfigError` with path and field context.

Alternative considered: leave `load_strategy_config()` exposing raw `ValidationError` and `OSError`. That keeps existing behavior but fails the clear configuration error requirement.

## Risks / Trade-offs

- `ConfigError` lives in `vela_core.config`, so `strategy_config.py` will import from that module -> keep `config.py` free of imports from `strategy_config.py` to avoid cycles.
- Removing public exports can affect callers that adopted the envelope after the prior commit -> acceptable because the envelope was introduced in the immediately preceding correction and is not the formal strategy contract.

## Context

Vela already contains `config/etf_pool.yaml`, but it is not loaded through a typed application-level schema. Existing market data workflows currently read active ETFs from the database, so this change should establish configuration parsing and validation without changing market data fetch behavior.

This change defines an application-level strategy envelope that future signal generation and backtesting can consume, while leaving algorithm-specific parameters flexible. It does not replace the existing concrete `strategy-configuration` capability for `config/strategy_v1.yaml`.

## Goals / Non-Goals

**Goals:**

- Provide Pydantic models for ETF pool and strategy envelope YAML configuration.
- Provide public loader functions that return typed config objects.
- Validate duplicate ETF entries by `exchange` and `symbol` within a pool.
- Wrap YAML parsing and Pydantic validation failures in `ConfigError` with the file path and field path.
- Keep the strategy envelope config schema conservative and algorithm-neutral.

**Non-Goals:**

- Do not change market data fetch workflows to source ETFs directly from YAML.
- Do not define a specific ETF rotation algorithm or concrete momentum/rebalance parameters.
- Do not add database persistence for configuration files.
- Do not introduce a new configuration format beyond YAML.

## Decisions

### Use YAML as the configuration format

Use YAML for ETF pool and strategy envelope configuration because the existing ETF pool file is already YAML and the project already treats configuration as human-edited files.

Alternative considered: support both JSON and YAML. This adds loader branching and test surface without solving a current need.

### Keep ETF exchange as an unrestricted string

`exchange` should be typed as `str`, not a strict enum. The current pool uses `SSE` and `SZSE`, but allowing other exchange codes avoids schema churn when the ETF universe expands.

Alternative considered: restrict to `SSE | SZSE`. That catches typos earlier, but it also bakes the current pool into the schema.

### Detect duplicate ETF entries by exchange and symbol

The ETF pool schema should reject duplicate entries with the same `(exchange, symbol)` pair. This matches the existing `ETFInfo` database identity and avoids rejecting same-symbol ETFs listed on different exchanges.

Alternative considered: reject duplicates by `symbol` only. That is simpler but inconsistent with the database model.

### Keep strategy envelope config conservative

Strategy envelope configuration should include stable identity fields such as `strategy_name`, `config_version`, and `universe_pool_id`, plus a generic `parameters` mapping. This gives future strategy workflows a typed object without prematurely defining algorithm-specific fields.

Alternative considered: define fields such as momentum windows, rebalance frequency, top-N selection, and weight caps now. Those may be useful later, but the strategy engine does not exist yet.

### Wrap load failures in ConfigError

Loader functions should catch YAML parsing errors, file read errors, and Pydantic validation errors, then raise `ConfigError`. The message should include the config file path and field path, while preserving the original exception as the cause.

Alternative considered: expose raw `ValidationError` directly. That is simpler, but it gives callers less consistent error handling and produces messages that are less useful in CLI output.

## Risks / Trade-offs

- Conservative `StrategyEnvelopeConfig.parameters` allows invalid algorithm-specific values until a concrete strategy schema exists -> add stricter strategy-specific schemas when strategy generation is implemented.
- Unrestricted `exchange` permits typo values -> rely on duplicate validation now and add exchange normalization only when multiple market regions are introduced.
- Config schemas are not yet connected to database seeding or market data fetch workflows -> keep this change focused, then add separate changes for config-driven import or workflow integration.

## 1. Configuration Service Tests

- [x] 1.1 Add a test that loading `config/strategy_v1.yaml` returns a typed aggregate configuration object.
- [x] 1.2 Add a test that the aggregate object contains the typed `StrategyConfig` and `ETFPoolConfig` values from the checked-in YAML files.
- [x] 1.3 Add a test that a relative `universe_config` path can be resolved from the repository working directory.
- [x] 1.4 Add a test that a relative `universe_config` path can fall back to the strategy config file directory.
- [x] 1.5 Add a test that a missing referenced ETF pool raises `ConfigError` with the missing ETF pool path.
- [x] 1.6 Add a test that an invalid referenced ETF pool raises `ConfigError` with the ETF pool path and failing field path.

## 2. Core Implementation

- [x] 2.1 Add a typed aggregate configuration model containing `strategy: StrategyConfig` and `etf_pool: ETFPoolConfig`.
- [x] 2.2 Implement a public `load_app_config(strategy_config_path: str | Path)` service entrypoint.
- [x] 2.3 Resolve `strategy.universe_config` relative to the current working directory first and the strategy config file directory second.
- [x] 2.4 Reuse existing `load_strategy_config()`, `load_etf_pool_config()`, and `ConfigError` behavior.
- [x] 2.5 Export the new aggregate model and loader from `vela_core`.

## 3. Verification

- [x] 3.1 Run `uv run pytest packages/core/tests/test_config.py packages/core/tests/test_strategy_config.py -q`.
- [x] 3.2 Run `openspec status --change "implement-config-loading-service"` and confirm the change is apply-ready.

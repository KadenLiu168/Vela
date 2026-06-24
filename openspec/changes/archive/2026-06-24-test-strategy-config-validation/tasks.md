## 1. Validation Test Coverage

- [x] 1.1 Add or adjust tests for representative valid strategy configuration input.
- [x] 1.2 Add or adjust tests for representative invalid strategy configuration input.
- [x] 1.3 Assert schema validation failure details for invalid direct `StrategyConfig.model_validate(...)` cases.
- [x] 1.4 Assert loader-wrapped `ConfigError` messages include the config path and failing field path.

## 2. Verification

- [x] 2.1 Run `uv run pytest packages/core/tests/test_strategy_config.py -q`.
- [x] 2.2 Run `uv run pytest`.
- [x] 2.3 Run project lint/type-check commands if present.
- [x] 2.4 Run OpenSpec validation for `test-strategy-config-validation`.

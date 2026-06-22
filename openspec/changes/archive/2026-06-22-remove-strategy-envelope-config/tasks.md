## 1. Tests

- [x] 1.1 Remove strategy envelope tests from core config tests.
- [x] 1.2 Add ETF pool validation error coverage that raises `ConfigError`.
- [x] 1.3 Add strategy loader tests for missing file, YAML parse, missing required field, and invalid nested field `ConfigError` behavior.

## 2. Core Implementation

- [x] 2.1 Remove `StrategyEnvelopeConfig` and `load_strategy_envelope_config()` from `vela_core.config`.
- [x] 2.2 Remove strategy envelope exports from `vela_core.__init__`.
- [x] 2.3 Update `load_strategy_config()` to wrap read, YAML parse, and validation failures in `ConfigError`.
- [x] 2.4 Keep `StrategyConfig` as the only strategy configuration model.

## 3. Specification Cleanup

- [x] 3.1 Update application configuration purpose and remove strategy envelope behavior from main specs through this change.
- [x] 3.2 Add strategy configuration loader error reporting behavior through this change.

## 4. Verification

- [x] 4.1 Run targeted config tests.
- [x] 4.2 Run the full test suite.
- [x] 4.3 Run ruff, mypy, and OpenSpec strict validation.

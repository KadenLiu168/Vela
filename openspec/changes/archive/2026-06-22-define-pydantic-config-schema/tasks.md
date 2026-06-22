## 1. Tests

- [x] 1.1 Add core tests for loading the existing ETF pool YAML into an `ETFPoolConfig`.
- [x] 1.2 Add core tests for ETF duplicate validation by `exchange` and `symbol`.
- [x] 1.3 Add core tests proving the same `symbol` on different `exchange` values is accepted.
- [x] 1.4 Add core tests for loading a conservative strategy envelope YAML into a `StrategyEnvelopeConfig`.
- [x] 1.5 Add core tests for `ConfigError` messages covering validation, YAML parse, and missing file failures.

## 2. Config Schema

- [x] 2.1 Add a `vela_core.config` module with Pydantic models for ETF entries, ETF pools, and strategy envelope configuration.
- [x] 2.2 Implement duplicate ETF validation using the `(exchange, symbol)` pair.
- [x] 2.3 Keep ETF `exchange` as an unrestricted string.
- [x] 2.4 Keep strategy-specific values in an algorithm-neutral `parameters` mapping.

## 3. Config Loading

- [x] 3.1 Implement YAML loading helpers for ETF pool and strategy envelope config paths.
- [x] 3.2 Add `ConfigError` and wrap file read, YAML parse, and Pydantic validation failures.
- [x] 3.3 Format validation errors with the config file path and failing field path.
- [x] 3.4 Export public config models, loaders, and `ConfigError` from the core package as appropriate.

## 4. Verification

- [x] 4.1 Run targeted core config tests.
- [x] 4.2 Run the full test suite.
- [x] 4.3 Run ruff checks for touched Python files.

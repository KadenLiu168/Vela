## Why

Vela already has typed schemas and individual YAML loaders for ETF pool and strategy configuration, but callers still need to coordinate multiple files themselves. A small configuration loading service gives strategy generation and backtesting a single, typed entrypoint with consistent error reporting before those workflows depend on configuration data.

## What Changes

- Add an application configuration loading service in the core package.
- Load a strategy configuration from a caller-provided path.
- Resolve and load the ETF pool referenced by the strategy configuration's `universe_config`.
- Return one typed aggregate object containing both the strategy configuration and ETF pool configuration.
- Preserve project-level `ConfigError` behavior for missing files, YAML parse failures, and schema validation failures.
- Keep the existing YAML file shapes unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `application-configuration`: Add a typed application configuration loading service that combines strategy and ETF pool configuration.

## Impact

- Affected core package: `packages/core/src/vela_core/config.py` and public exports in `packages/core/src/vela_core/__init__.py`.
- Affected tests: focused core configuration tests under `packages/core/tests/`.
- Related existing module: `packages/core/src/vela_core/strategy_config.py`.
- No database migration, CLI command, API endpoint, external dependency, or config file format change is introduced.

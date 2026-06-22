## Why

Vela currently has YAML configuration for the ETF pool, but no typed schema or shared loader to validate configuration before runtime workflows depend on it. Phase 1 also needs a conservative strategy envelope configuration contract so future signal generation and backtesting can consume stable typed objects without prematurely locking in a specific strategy algorithm.

## What Changes

- Add Pydantic schemas for YAML-based ETF pool configuration.
- Add a conservative Pydantic strategy envelope configuration schema with stable identity fields and a generic parameters mapping.
- Add loader behavior that returns typed configuration objects from YAML files.
- Add clear configuration failure behavior through a project-level `ConfigError` that includes the config file path and validation field path.
- Reject duplicate ETF entries within one pool by the pair of `exchange` and `symbol`.

## Capabilities

### New Capabilities

- `application-configuration`: Defines typed YAML configuration loading and validation for ETF pool and strategy envelope configuration.

### Modified Capabilities

- None.

## Impact

- Affects `packages/core` by adding configuration schemas, load functions, and config-specific errors.
- Affects tests by adding coverage for successful loading, duplicate ETF validation, and clear validation error messages.
- Uses existing dependencies: `pydantic` and YAML parsing support already present through the project environment.

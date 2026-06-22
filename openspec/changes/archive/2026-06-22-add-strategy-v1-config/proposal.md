## Why

Vela needs a versioned strategy configuration before signal generation and backtesting can share the same parameter contract. A checked-in `strategy_v1.yaml` plus schema validation keeps early strategy experiments reproducible without implementing the strategy engine yet.

## What Changes

- Add a `config/strategy_v1.yaml` file that defines the initial ETF rotation strategy parameters.
- Add a Pydantic schema for strategy configuration validation.
- Cover required parameters for momentum windows, score weights, Top N selection, defensive asset behavior, and transaction costs.
- Add tests proving the checked-in strategy config loads and validates successfully.
- Add tests for invalid configurations that should be rejected.

## Capabilities

### New Capabilities

- `strategy-configuration`: Versioned strategy configuration files and Pydantic validation for ETF rotation strategy parameters.

### Modified Capabilities

- None.

## Impact

- Affected config: `config/strategy_v1.yaml`.
- Affected core package: strategy configuration schema and loader under `packages/core/src/vela_core`.
- Affected tests: focused core tests for valid and invalid strategy configuration validation.
- No database migration, CLI command, API endpoint, or strategy calculation behavior is introduced by this change.

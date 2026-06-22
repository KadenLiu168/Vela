## Why

The current strategy configuration schema validates that momentum windows are positive and score weights sum to 1.0, but it does not fully protect the assumptions needed by the ETF rotation scoring calculation. Tightening this contract now prevents invalid strategy parameters from reaching future signal generation and backtesting code.

## What Changes

- Require the short momentum window to be strictly shorter than the long momentum window.
- Require each score weight to be positive and keep the existing normalized total weight requirement.
- Add focused tests for invalid momentum window relationships and invalid individual score weights.
- Keep the existing `config/strategy_v1.yaml` shape unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `strategy-configuration`: Strengthen validation requirements for momentum window relationships and score weight legality.

## Impact

- Affected core package: `packages/core/src/vela_core/strategy_config.py`
- Affected tests: `packages/core/tests/test_strategy_config.py`
- Affected specs: `openspec/specs/strategy-configuration/spec.md`
- No database migration, CLI command, API endpoint, or strategy calculation implementation is introduced.

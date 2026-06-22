## Why

The current strategy configuration schema protects basic field shape, but strategy calculation still depends on stronger assumptions: momentum windows must be ordered, score weights must keep both configured components active, and the defensive fallback asset must be tradable. Tightening this contract now prevents invalid strategy parameters from reaching future signal generation and backtesting code.

## What Changes

- Require the short momentum window to be strictly shorter than the long momentum window.
- Require each score weight to be positive and keep the existing normalized total weight requirement.
- Validate that the configured defensive asset exists in the strategy universe ETF pool and is active.
- Add focused tests for invalid momentum relationships, invalid individual score weights, and defensive asset fallback legality.
- Keep the existing `config/strategy_v1.yaml` shape unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `strategy-configuration`: Strengthen validation requirements for momentum window relationships, score weight legality, and defensive asset fallback tradability.

## Impact

- Affected core package: `packages/core/src/vela_core/strategy_config.py`
- Affected tests: `packages/core/tests/test_strategy_config.py`
- Affected specs: `openspec/specs/strategy-configuration/spec.md`
- No database migration, CLI command, API endpoint, external dependency, or strategy calculation implementation is introduced.

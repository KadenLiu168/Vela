## Why

Backtesting needs strategy signals on historical rebalance dates, not only the latest or one manually requested date. Generating those signals through the existing strategy logic keeps historical portfolio calculations aligned with live signal behavior while avoiding future data.

## What Changes

- Add a core historical signal generation helper that derives rebalance dates from historical trading dates and generates one signal per rebalance date.
- Reuse the existing single-date strategy signal generation pipeline for each historical rebalance date.
- Keep generated results persisted through the existing `StrategySignal` and `StrategySignalPosition` contract so later portfolio holding calculations can read target weights.
- Do not add a backtest engine, portfolio holding calculator, CLI command, database schema change, or new strategy rules.

## Capabilities

### New Capabilities

### Modified Capabilities
- `strategy-signal-generation`: Add historical rebalance-date signal generation using existing strategy logic without future data.

## Impact

- Affected core package: `packages/core/src/vela_core/strategy_signal_generation.py`
- Affected public exports: `packages/core/src/vela_core/__init__.py`
- Affected tests: `packages/core/tests/test_strategy_signal_generation.py`
- Affected specs: `openspec/specs/strategy-signal-generation/spec.md`
- No database migration, CLI change, API endpoint, external dependency, or portfolio holding implementation is introduced.

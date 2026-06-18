## Why

`StrategySignalPosition` already records ETF position details for a strategy signal run, but the ORM contract only exposes database foreign keys. Backend code should be able to navigate the signal-to-positions relationship directly through SQLAlchemy model attributes.

## What Changes

- Add an explicit ORM relationship from `StrategySignal` to its position rows.
- Add the inverse ORM relationship from `StrategySignalPosition` back to its parent `StrategySignal`.
- Keep the existing `StrategySignalPosition` model name and `strategy_signal_position` table.
- Keep existing foreign keys, uniqueness rules, and no delete cascade behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-signal-model`: Require explicit ORM object relationships between `StrategySignal` and `StrategySignalPosition`.

## Impact

- Affected code: `packages/core/src/vela_core/models/strategy_signal.py`.
- Affected tests: focused ORM relationship tests for `StrategySignal.positions` and `StrategySignalPosition.strategy_signal`.
- No database migration is expected because SQLAlchemy `relationship()` changes the Python ORM mapping, not the table schema.

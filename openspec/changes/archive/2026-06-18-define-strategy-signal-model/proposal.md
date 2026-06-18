## Why

Vela needs durable strategy signal storage before strategy generation and backtesting workflows can share the same output records. The model should preserve run history while keeping the first persistence contract small and queryable.

## What Changes

- Add a SQLAlchemy `StrategySignal` ORM model for one strategy signal generation run.
- Add a SQLAlchemy `StrategySignalPosition` ORM model for target position details produced by a signal run.
- Record signal date, configuration version, generation timestamp, execution status, strategy result, optional error message, and audit timestamps.
- Allow multiple runs for the same signal date and configuration version so retries, failures, and data-correction reruns are preserved.
- Track target ETF positions with target weight plus optional rank and score explanation fields.
- Prevent duplicate ETF rows within the same signal run.

## Capabilities

### New Capabilities

- `strategy-signal-model`: SQLAlchemy ORM models and persistence contract for strategy signal runs and their target position details.

### Modified Capabilities

None.

## Impact

- Core models: adds `StrategySignal` and `StrategySignalPosition` under `packages/core/src/vela_core/models`.
- Alembic: adds a migration for the new strategy signal tables, constraints, and indexes.
- Tests: adds focused model and migration-adjacent schema coverage under `packages/core/tests`.

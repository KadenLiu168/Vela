## Why

COP-52 needs generated strategy signals to be durable and queryable instead of leaving callers to assemble `StrategySignal` and `StrategySignalPosition` rows by hand. The existing models already preserve run history, but the core package does not yet provide a small persistence contract for writing a signal with positions or reading the latest successful signal.

## What Changes

- Add a core persistence helper that writes one `StrategySignal` row and its `StrategySignalPosition` rows in the same session.
- Keep repeated generation for the same `signal_date` and `config_version` explicit by creating another run history row instead of overwriting prior runs.
- Add a query helper that returns the latest successful signal for a date and config version with its positions loaded.
- Export the new persistence result/input types and helper functions from `vela_core`.
- Add focused tests for write behavior, repeated same-date generation, and latest successful query behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-signal-model`: Extend the persistence contract from ORM tables to focused write and latest-query helpers for strategy signal runs and positions.

## Impact

- Core package: adds a small strategy signal persistence module under `packages/core/src/vela_core`.
- Public API: exports persistence helper types and functions from `vela_core.__init__`.
- Tests: adds focused coverage under `packages/core/tests`.
- OpenSpec: updates the `strategy-signal-model` capability without changing database schema.

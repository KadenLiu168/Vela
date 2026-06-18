## 1. Tests

- [x] 1.1 Add a focused test proving `StrategySignal.positions` returns the related `StrategySignalPosition` rows.
- [x] 1.2 Add a focused test proving `StrategySignalPosition.strategy_signal` returns the parent `StrategySignal`.

## 2. ORM Model

- [x] 2.1 Add typed SQLAlchemy `relationship()` attributes for `StrategySignal.positions` and `StrategySignalPosition.strategy_signal`.
- [x] 2.2 Keep the existing table schema, foreign keys, constraints, and public `StrategySignalPosition` model name unchanged.

## 3. Verification

- [x] 3.1 Run the focused strategy signal model tests.
- [x] 3.2 Run OpenSpec validation for `add-strategy-signal-position-relationship`.

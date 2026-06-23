## 1. Specification Validation

- [x] 1.1 Run `openspec status --change "persist-latest-strategy-signal"` and confirm the change is apply-ready.

## 2. Persistence Tests

- [x] 2.1 Add tests that persisting a signal writes the parent `StrategySignal` and child `StrategySignalPosition` rows.
- [x] 2.2 Add tests that persisting a signal with no positions writes only the parent signal.
- [x] 2.3 Add tests that two same-date and same-config writes create two distinct signal runs.
- [x] 2.4 Add tests that latest successful query returns the newest successful run with positions.
- [x] 2.5 Add tests that latest successful query ignores newer non-success runs and returns `None` when no success exists.

## 3. Core Implementation

- [x] 3.1 Add input/result dataclasses for strategy signal persistence.
- [x] 3.2 Implement the helper that persists one signal and its positions without committing the caller's session.
- [x] 3.3 Implement the helper that queries the latest successful signal by signal date and config version.
- [x] 3.4 Export the new types and helper functions from `vela_core`.

## 4. Verification

- [x] 4.1 Run the focused strategy signal persistence tests.
- [x] 4.2 Run core package tests.
- [x] 4.3 Run lint, type check, and OpenSpec validation.

## 1. Dashboard Backfill

- [x] 1.1 Load structured latest signal data after successful Dashboard signal generation.
- [x] 1.2 Backfill the Dashboard latest signal summary from the structured latest signal response when available.
- [x] 1.3 Keep signal-generation failure handling local and avoid partial inconsistent Dashboard state.

## 2. Tests

- [x] 2.1 Update Dashboard generation tests to require `GET /api/strategy-signals/latest` after successful generation.
- [x] 2.2 Add coverage that Dashboard and Signal Detail render the same persisted latest signal values.
- [x] 2.3 Add coverage that browser refresh restores Dashboard latest signal status from backend data.

## 3. Validation

- [x] 3.1 Run focused frontend tests for the Dashboard and Signal Detail flow.
- [x] 3.2 Run frontend typecheck, lint, and test suite.
- [x] 3.3 Run full project tests if feasible and OpenSpec validation.

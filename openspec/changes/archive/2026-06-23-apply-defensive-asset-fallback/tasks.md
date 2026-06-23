## 1. Core Selection Behavior

- [x] 1.1 Add a fallback-aware selection result type and selection function in `momentum_scoring`.
- [x] 1.2 Export the fallback-aware selection API from `vela_core`.

## 2. Tests

- [x] 2.1 Add a unit test for fallback when ranked ETF candidates are fewer than `selection.top_n`.
- [x] 2.2 Add a unit test confirming fallback does not apply when ranked ETF candidates satisfy `selection.top_n`.

## 3. Validation

- [x] 3.1 Run focused momentum scoring tests.
- [x] 3.2 Run applicable project tests, lint, formatting check, and OpenSpec validation.

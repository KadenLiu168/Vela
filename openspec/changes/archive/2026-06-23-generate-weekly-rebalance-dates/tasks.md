## 1. Core Implementation

- [x] 1.1 Add a pure core helper that returns the last available input trading date for each ISO week.
- [x] 1.2 Export the helper from `vela_core`.

## 2. Tests

- [x] 2.1 Add unit tests for normal weekly generation, holiday or missing-date gaps, duplicate or unsorted input, and empty input.

## 3. Validation

- [x] 3.1 Run focused unit tests for weekly rebalance date generation.
- [x] 3.2 Run project test, lint, format-check, and OpenSpec validation commands.

## 1. Tests

- [x] 1.1 Add a unit test proving ranked momentum scores are ordered by weighted score descending.
- [x] 1.2 Add a unit test proving equal weighted scores are ordered by ETF id ascending.
- [x] 1.3 Add a unit test proving momentum scores with `score=None` are excluded from ranked results.
- [x] 1.4 Add a unit test proving ranks are continuous 1-based integers after missing scores are excluded.
- [x] 1.5 Add a unit test proving slicing the ranked results by `config.selection.top_n` returns the expected highest-ranked ETF ids.

## 2. Core Implementation

- [x] 2.1 Add a frozen ranking result dataclass with ETF id, as-of date, weighted score, and rank.
- [x] 2.2 Add a pure ranking function that accepts existing `MomentumScore` values and returns ranked results.
- [x] 2.3 Filter out `MomentumScore` values whose `score` is `None`.
- [x] 2.4 Sort eligible scores by `score` descending and ETF id ascending.
- [x] 2.5 Assign continuous 1-based ranks in sorted order.

## 3. Public API

- [x] 3.1 Export the ranking result type from `vela_core`.
- [x] 3.2 Export the ranking function from `vela_core`.

## 4. Verification

- [x] 4.1 Run `uv run pytest packages/core/tests/test_momentum_scoring.py`.
- [x] 4.2 Run `uv run pytest packages/core/tests`.

## 1. Tests

- [x] 1.1 Add a unit test proving configured Top N selection returns the highest-ranked ETF ids.
- [x] 1.2 Add a unit test proving each selected ETF includes ETF id, rank, score, and equal target weight.
- [x] 1.3 Add a unit test proving insufficient ranked ETFs return all available ETFs with weights across the actual selection count.
- [x] 1.4 Add a unit test proving an empty ranking list returns an empty selection.

## 2. Core Implementation

- [x] 2.1 Add a frozen Top N selection result dataclass with ETF id, rank, score, and target weight.
- [x] 2.2 Add a pure function that accepts ranked momentum results and strategy config, then returns selected Top N results.
- [x] 2.3 Ensure target weights are based on the actual selected count.

## 3. Public API

- [x] 3.1 Export the selection result type from `vela_core`.
- [x] 3.2 Export the selection function from `vela_core`.

## 4. Verification

- [x] 4.1 Run `uv run pytest packages/core/tests/test_momentum_scoring.py`.
- [x] 4.2 Run `uv run pytest packages/core/tests`.
- [x] 4.3 Run `uv run pytest`.
- [x] 4.4 Run `uv run ruff check .`.
- [x] 4.5 Run formatting checks.
- [x] 4.6 Run OpenSpec validation for `select-top-n-etfs`.

Note: `uv run ruff format --check .` was executed and reports pre-existing
formatting differences in unrelated files outside this change. The files touched
by this change pass `uv run ruff format --check
packages/core/src/vela_core/momentum_scoring.py packages/core/src/vela_core/__init__.py
packages/core/tests/test_momentum_scoring.py`.

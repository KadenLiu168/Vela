## 1. Confirm Removal Boundaries

- [x] 1.1 Repeat exact-symbol searches for `ResolvedAdjustedPrice`, `resolved_adjusted_prices`, `_allocate_target`, `_rebalance`, `SUPPORTED_EVIDENCE_VERSIONS`, and the six unversioned evidence aliases; verify the only consumers are the definitions and dedicated projection test recorded by this Change before editing.
- [x] 1.2 Record the canonical surfaces that must remain (`forward_adjusted_prices`, `ResolvedSessionPrice`, `_allocate_target_weights`, `_rebalance_target`, the three `EVIDENCE_VERSION*` constants, versioned evidence models, and `validate_wf_evidence`) and verify each has active source or test references.

## 2. Remove Unused Core Surfaces

- [x] 2.1 Remove `ResolvedAdjustedPrice`, `resolved_adjusted_prices()`, their test import, and their dedicated test without changing `forward_adjusted_prices()`; verify with `uv run pytest packages/core/tests/test_adjusted_price_projection.py`.
- [x] 2.2 Remove only `_allocate_target()` and `_rebalance()` from `strategy_equity_curve.py`, leaving their target-weight callees unchanged; verify with `uv run pytest packages/core/tests/test_strategy_equity_curve.py`.
- [x] 2.3 Remove `SUPPORTED_EVIDENCE_VERSIONS` and the six unversioned aliases only from `walk_forward/evidence.py`; verify version dispatch and persisted evidence behavior with `uv run pytest packages/core/tests/test_walk_forward_evidence_contract.py packages/core/tests/test_walk_forward_integration.py packages/core/tests/test_walk_forward_report_persistence.py`.

## 3. Verify Behavior and Scope

- [x] 3.1 Repeat the exact-symbol scan and verify every removed name has zero remaining references while the canonical surfaces from task 1.2 remain present and referenced.
- [x] 3.2 Run the complete Python CI-equivalent gate from the repository root: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`; verify every command succeeds without using the repository-root `vela.db`.
- [x] 3.3 Run `openspec validate prune-unused-core-surfaces --strict`, `openspec validate --all --strict`, `openspec doctor`, and `git diff --check`; verify the named Change and doctor pass, the all-target result introduces no failure beyond the recorded pre-Apply baseline of 11 existing placeholder-Purpose spec failures, and the complete status/diff limits implementation edits to the four-file allowlist plus Change task bookkeeping with no living specs, dependencies, database files, Web files, or unrelated work changed.

## Why

API backtest tests currently load the mutable checked-in strategy configuration and pin a derived `max_drawdown` value, so legitimate parameter edits or shared backtest-engine changes force unrelated API test updates. Configuration endpoint and loader tests also repeat point-in-time strategy values instead of separating configuration validity, serialization fidelity, workflow orchestration, and financial arithmetic contracts.

## What Changes

- Make checked-in configuration tests validate typed structure and cross-file consistency without duplicating mutable strategy parameter literals.
- Make `/api/config` tests derive expected strategy values independently from the loaded application configuration while still detecting serialization omissions or transformations.
- Inject an explicit deterministic strategy configuration into API tests that execute backtests, so production YAML edits do not change their fixtures, signal schedule, or metrics.
- Replace the API workflow's exact `max_drawdown` golden value with response-to-persistence equality and domain invariants.
- Keep exact drawdown and transaction-cost arithmetic in focused core tests, including cost/no-cost comparisons, so loosening the API assertion does not reduce financial regression coverage.
- Preserve the existing requirement that effective strategy parameter changes use a new configuration version; this Change does not change production strategy values, configuration paths, or versioning semantics.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite-validation`: Require deterministic test-owned strategy configuration for API backtest workflow tests and assign exact financial arithmetic assertions to focused core tests while configuration-facing tests derive mutable values from the loaded source.

## Impact

- Affected tests: `packages/core/tests/test_strategy_config.py`, `packages/core/tests/test_config.py`, `apps/api/tests/test_api_config.py`, `apps/api/tests/test_dashboard.py`, `apps/api/tests/test_strategy_signal_generate.py`, and the backtest execution cases in `apps/api/tests/test_backtest_run.py`.
- Existing focused metric and transaction-cost tests in `packages/core/tests/test_strategy_equity_curve.py` remain the exact numerical regression boundary and may receive only narrowly necessary coverage additions.
- No production API, persistence schema, strategy implementation, production YAML value, default configuration path, or runtime behavior changes.

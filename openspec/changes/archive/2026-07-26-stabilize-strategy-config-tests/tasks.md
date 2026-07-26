## 1. Establish the Regression Boundaries

- [x] 1.1 Run the current focused configuration, API backtest, and core equity-curve tests to record the pre-change baseline and confirm the API workflow is the only layer pinning its derived `max_drawdown`.
- [x] 1.2 Trace the existing focused maximum-drawdown and transaction-cost tests to the delta-spec scenarios, documenting whether deepest drawdown, entry/rebalance cost, different basis-point rates, and cost/no-cost behavior already have exact `Decimal` coverage.

## 2. Make Configuration-Facing Tests Follow the Loaded Source

- [x] 2.1 Refactor the checked-in strategy configuration smoke test to assert the validated strategy variant and structural contracts without copying mutable momentum, selection, defense, cost, performance, or rebalance values as point-in-time literals.
- [x] 2.2 Refactor the `/api/config` test to construct its expected strategy object independently from the loaded typed `AppConfig`, including type-aware parameters, costs, performance, and rebalance fields, without calling the production `_serialize_config` helper.
- [x] 2.3 Keep schema boundary tests based on explicit local fixtures so invalid cost, momentum, discriminator, and other validation cases remain precise and independent of the checked-in production configuration.
- [x] 2.4 Derive remaining checked-in loader and API pass-through identity expectations from the loaded `AppConfig` or source YAML instead of production `version`, pool, provider, or path literals.

## 3. Isolate API Backtest Workflow Inputs

- [x] 3.1 Add one validated test-owned dual-momentum configuration fixture/helper that explicitly fixes identity, parameter, defense, rebalance, transaction-cost, and risk-free-rate inputs used by API backtest execution scenarios.
- [x] 3.2 Patch `vela_api.main.load_strategy_config` only within the tests that execute `/api/backtests/run`, ensuring the run and follow-up detail requests share the same fixed configuration without changing production dependency injection.
- [x] 3.3 Ensure the SQLite fixture seeds every ETF and sufficient lookback data required by the fixed test configuration, and verify signal and curve counts against the persisted collections.
- [x] 3.4 Replace the exact API `max_drawdown` golden with parsing of the API decimal string, equality to the persisted `BacktestRun.max_drawdown`, and the domain invariant `-1 < max_drawdown <= 0`; retain response field and run/detail consistency assertions.

## 4. Preserve Exact Financial Coverage

- [x] 4.1 Keep the focused core maximum-drawdown and transaction-cost assertions exact; add only the smallest missing controlled regression identified by task 1.2 rather than duplicating the API workflow scenario.
- [x] 4.2 Verify that a negative drawdown is not used as evidence of cost deduction: cost coverage must compare cost/no-cost paths or assert exact turnover-rate arithmetic.
- [x] 4.3 Confirm no production strategy configuration value, version, default path, strategy implementation, API schema, or persistence code changed as part of this test-only implementation.

## 5. Validate the Change

- [x] 5.1 Run `uv run pytest packages/core/tests/test_strategy_config.py apps/api/tests/test_api_config.py apps/api/tests/test_backtest_run.py` and confirm all configuration and API workflow tests pass.
- [x] 5.2 Run `uv run pytest packages/core/tests/test_strategy_equity_curve.py` and confirm exact drawdown and transaction-cost regression coverage passes.
- [x] 5.3 Run the complete affected backend suites plus repository Ruff format/lint and mypy gates, fixing only failures caused by this Change.
- [x] 5.4 Run `openspec validate stabilize-strategy-config-tests --strict` and trace every delta-spec scenario to implementation and executable test evidence.

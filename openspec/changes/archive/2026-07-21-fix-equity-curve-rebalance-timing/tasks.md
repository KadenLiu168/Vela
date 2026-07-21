## 1. Rebalance-Timing Regression Coverage

- [x] 1.1 Rewrite the crash-at-rebalance regression so the interval ending on 2026-06-25 asserts the prior SPY 60% / QQQ 40% allocation, `daily_return=-0.260000`, and `net_value=0.754800`.
- [x] 1.2 Extend the rebalance regression through one additional trading date and assert that QQQ 100% earns only the first complete close-to-close interval after its snapshot becomes effective.
- [x] 1.3 Correct the carried/rebalanced-holdings regression expectations so the SPY loss before the snapshot transition cannot be replaced by QQQ's return.
- [x] 1.4a Add SPY price on 2026-06-24 (close_price=110) to `test_calculate_strategy_equity_curve_deducts_rebalance_transaction_cost` so the old SPY holding earns +10% market return during the transition interval. Assertions remain `daily_return=0.098000, net_value=1.098000` (same numeric result, now earned by SPY instead of QQQ).
- [x] 1.4b Add SPY price on 2026-06-24 (close_price=110) to `test_calculate_strategy_equity_curve_applies_different_cost_rates` so the old SPY holding earns +10% market return during the transition interval. Assert `low_cost daily_return=0.098000, net_value=1.098000` and `high_cost daily_return=0.095000, net_value=1.095000` after their respective 0.2% and 0.5% turnover costs.
- [x] 1.4c Add SPY price on 2026-06-24 (close_price=110) to `test_calculate_strategy_equity_curve_transaction_cost_reduces_net_value` for the same reason. Assertions remain `no_cost daily_return=0.100000, net_value=1.100000` and `cost daily_return=0.098000, net_value=1.098000`.
- [x] 1.5 Run `uv run pytest -p no:cacheprovider packages/core/tests/test_strategy_equity_curve.py -q` before the production change and confirm these rebalance regressions fail for the intended look-ahead reason: `test_calculate_strategy_equity_curve_verifies_daily_values_and_rebalance_effect` (including its post-rebalance interval) and `test_calculate_strategy_equity_curve_carries_and_rebalances_holdings`.

## 2. Equity-Curve Return Attribution

- [x] 2.1 In `_calculate_daily_return` in `packages/core/src/vela_core/strategy_equity_curve.py`, change the market-return loop from `snapshot.holdings` to `previous_snapshot.holdings`. The remaining loop body (price lookup using `previous_date` and `snapshot.trade_date`, missing-price guard) and the `_calculate_turnover(previous_snapshot, snapshot)` call remain unchanged.
- [x] 2.2 Add or refine a concise code comment documenting that point `i` represents the close-to-close interval from `i-1` to `i`, with market return attributed to the interval-start snapshot and turnover charged at the snapshot transition.
- [x] 2.3 Confirm initial entry still earns no pre-entry market return (verified by `test_calculate_strategy_equity_curve_deducts_initial_entry_transaction_cost` where `previous_snapshot` is empty), still charges configured entry turnover, and unchanged holdings still incur no transaction cost (verified by `test_calculate_strategy_equity_curve_applies_weighted_daily_return` where consecutive snapshots carry identical holdings).

## 3. Verification

- [x] 3.1 Run `uv run pytest -p no:cacheprovider packages/core/tests/test_strategy_equity_curve.py -q` and confirm all focused equity-curve tests pass.
- [x] 3.2 Run `uv run pytest -p no:cacheprovider packages/core/tests -q` and confirm the complete core test suite passes.
- [x] 3.3 Run `uv run ruff check packages/core/src/vela_core/strategy_equity_curve.py packages/core/tests/test_strategy_equity_curve.py`, `uv run ruff format --check packages/core/src/vela_core/strategy_equity_curve.py packages/core/tests/test_strategy_equity_curve.py`, and `uv run mypy packages/core/src/vela_core/strategy_equity_curve.py`; resolve only issues caused by this change. (The repository's mypy configuration covers source packages, not tests.)
- [x] 3.4 Review the final diff to confirm `portfolio_holdings` T+1 selection, missing-price neutrality, turnover definition, quantization, public interfaces, and database schemas remain unchanged.

## 4. Historical Result Boundary

- [x] 4.1 Confirm the implementation does not mutate existing `BacktestRun` or `BacktestEquityCurve` rows and does not add a schema, API, or CLI contract for stale-result identification.
- [x] 4.2 Record that historical-result inspection, labeling, deletion, and bulk reruns are excluded from Apply. If product-visible distinction or remediation is required, create a separate Change covering the model, migration, API, UI, and an explicitly approved operational runbook.

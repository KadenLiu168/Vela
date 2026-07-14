## 1. Signal Selection Fix

- [x] 1.1 In `packages/core/src/vela_core/portfolio_holdings.py`, change the while-loop condition from `signal_dates[next_signal_index] <= trade_date` to `< trade_date` (line 48) so a signal is applied strictly after its as-of day (T+1).
- [x] 1.2 Confirm `_latest_successful_signals_by_date`'s query bound `signal_date <= through_date` (line 69) still fetches every needed prior signal with no change required; document the reasoning in code comment if helpful.

## 2. Test Rewrites (packages/core/tests/test_portfolio_holdings.py)

- [x] 2.1 `test_calculate_daily_holdings_from_signal_positions`: the only signal is dated 06-23 and the only `trade_date` is 06-23, so after the fix the snapshot is empty. Assert `snapshots[0].signal_date is None`, `snapshots[0].strategy_signal_id is None`, and `snapshots[0].holdings == []` (drop the prior same-day position/weight assertions, which no longer hold under T+1).
- [x] 2.2 `test_calculate_interval_holdings_carries_positions_forward`: for signal dated 06-23 over [06-23, 06-24, 06-25], assert 06-23 -> empty, 06-24/06-25 -> 06-23 signal.
- [x] 2.3 `test_calculate_interval_holdings_empty_before_first_signal`: for signal dated 06-24 over [06-23, 06-24], assert BOTH dates are empty - `signal_date is None`, `strategy_signal_id is None`, and `holdings == []` for each snapshot (06-23 precedes the first signal; 06-24 is the signal's own day and is not applied). Drop the prior assertion that `snapshots[1]` carried the 06-24 signal.
- [x] 2.4 `test_calculate_interval_holdings_changes_on_rebalance_date`: signals 06-23 (SPY) and 06-25 (QQQ) over [06-24, 06-25, 06-26] -> 06-24 SPY, 06-25 SPY (carry-forward), 06-26 QQQ (T+1).
- [x] 2.5 `test_calculate_holdings_uses_latest_successful_signal_run_for_date`: keep the two same-date runs (06-23: SPY early, QQQ later) and request trading dates `[06-23, 06-24]`. Assert (a) `snapshots[0]` for 06-23 has `signal_date is None` (no same-day application, T+1 semantic); and (b) `snapshots[1]` for 06-24 uses the LATEST run - `strategy_signal_id == latest.strategy_signal.id` and `holdings == [qqq.id]`. This preserves the "latest successful signal run wins" spec scenario at T+1, which the old same-day assertion no longer exercises after the fix.
- [x] 2.6 `test_calculate_holdings_ignores_failed_signals`: confirm it still passes unchanged (06-24 uses prior 06-23 success signal).

## 3. Test Rewrites (packages/core/tests/test_strategy_equity_curve.py)

These tests call `calculate_strategy_equity_curve`, which internally calls `calculate_portfolio_holdings`, so they transitively encode the old same-day (T+0) effectiveness in their `signal_date` vs `trade_dates` layout. The `<` fix is NOT applied through a mock here: after the fix, seven tests turn red and four more keep identical numbers only by coincidence (cost-zero / missing-price / empty-curve cases) while silently switching to a warmup-empty shape that no longer guards T+1.

- [x] 3.1 Apply one uniform rewrite to the `_add_signal(...)` calls in the eleven affected tests listed in 3.2/3.3: shift `signal_date` one calendar day earlier (06-23 -> 06-22, 06-24 -> 06-23, 06-25 -> 06-24). Leave `trade_dates`, prices, cost config, and ALL value assertions unchanged. Rationale: moving each signal one day before its first consuming `trade_date` makes that `trade_date` the signal's T+1, so holdings take effect at the same relative position in the curve as before. Because `calculate_strategy_equity_curve` compounds from `trading_dates[0]` and `_load_prices_by_key` keys prices by `trade_date` (not `signal_date`), every asserted `net_value` / `daily_return` is numerically unchanged.
- [x] 3.2 After 3.1, confirm the seven currently-red tests go green with unchanged assertions: `test_calculate_strategy_equity_curve_verifies_daily_values_and_rebalance_effect`, `test_calculate_strategy_equity_curve_carries_and_rebalances_holdings`, `test_calculate_strategy_equity_curve_deducts_initial_entry_transaction_cost`, `test_calculate_strategy_equity_curve_deducts_rebalance_transaction_cost`, `test_calculate_strategy_equity_curve_applies_different_turnover_costs`, `test_calculate_strategy_equity_curve_applies_different_cost_rates`, `test_calculate_strategy_equity_curve_transaction_cost_reduces_net_value`.
- [x] 3.3 After 3.1, confirm the four coincidence-passing tests still pass and now exercise T+1 rather than warmup-empty: `test_calculate_strategy_equity_curve_applies_weighted_daily_return`, `test_calculate_strategy_equity_curve_treats_missing_price_input_as_neutral`, `test_calculate_strategy_equity_curve_skips_transaction_cost_when_configured_zero`, `test_equity_curve_no_artificial_jump_on_ex_dividend_date`.
- [x] 3.4 Note the two entry-cost tests (`test_calculate_strategy_equity_curve_deducts_initial_entry_transaction_cost`, `test_calculate_strategy_equity_curve_skips_transaction_cost_when_configured_zero`) shift 06-24 -> 06-23, which preserves their intended warmup shape (06-23 empty, 06-24 first build) so the entry cost still lands on 06-24 with unchanged asserted values.
- [x] 3.5 Leave unchanged: `test_calculate_strategy_equity_curve_returns_empty_for_empty_dates`, `test_calculate_strategy_equity_curve_sets_initial_net_value` (single point), `test_calculate_strategy_equity_curve_keeps_net_value_for_empty_holdings` (no signal), and all pure-function tests for annualized return / max drawdown / volatility / Sharpe (they never call `calculate_strategy_equity_curve`).

## 4. Validation

- [x] 4.1 Run `pytest packages/core/tests/test_portfolio_holdings.py` and confirm all green.
- [x] 4.2 Run `pytest packages/core/tests/test_strategy_equity_curve.py` and confirm all green (this file is NOT mocked and transitively exercises the fix).
- [x] 4.3 Run `pytest packages/core/tests/test_backtest_runner.py` and confirm still green (it mocks `calculate_portfolio_holdings` and `calculate_strategy_equity_curve`).
- [x] 4.4 Run the full test suite (`packages/core`, `apps/api`, `apps/cli`, `tests/`) and confirm no other test turns red. Expected-unaffected areas (verified during review): `test_backtest_runner.py` (mocked); `apps/api/tests/test_backtest_run.py` and `test_p0_workflow.py` (assert only non-None / API-vs-DB consistency, not specific metric values); `apps/cli/tests/test_run_backtest.py` (mocks `run_backtest`); `tests/integration_data.py` (hardcoded seed rows inserted via `session.add`, not computed by the equity-curve pipeline).
- [x] 4.5 Run ruff and mypy on `packages/core/src/vela_core/portfolio_holdings.py` with no new violations.

## 5. Operational Follow-up (owner: user, out of code scope)

- [ ] 5.1 Re-run all historical backtests so persisted results in `vela.db` reflect T+1-correct (non-look-ahead) numbers; treat pre-fix runs as stale.

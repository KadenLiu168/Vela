## 1. Core holdings query scoping

- [x] 1.1 Add failing tests asserting `calculate_portfolio_holdings` accepts `signal_ids`, restricts signals to that set (ignores signals outside it, including newer runs for the same date), and returns empty holdings for an explicitly supplied empty collection.
- [x] 1.2 Update `_latest_successful_signals_by_date` (`portfolio_holdings.py`) to accept `signal_ids: Sequence[int] | None`; when the value is not `None`, query `WHERE StrategySignal.id IN (signal_ids)` instead of global latest-wins, with an empty collection returning no signals without issuing `IN ()`; when `None`, preserve existing behavior.
- [x] 1.3 Update `calculate_portfolio_holdings` signature to accept optional `signal_ids` and thread it into the query helper.
- [x] 1.4 Handle an empty `signal_ids` collection safely as an explicitly scoped zero-signal result (do not issue `IN ()` and do not fall back to global selection).

## 2. Equity curve signal scoping

- [x] 2.1 Update `calculate_strategy_equity_curve` signature (`strategy_equity_curve.py`) to accept optional `signal_ids: Sequence[int] | None = None` and pass it through to the internal `calculate_portfolio_holdings` call.
- [x] 2.2 Add failing test in `test_strategy_equity_curve.py` with conflicting same-date signals that asserts the `signal_ids`-scoped curve has the expected points from the selected signal set, rather than merely differing from global latest-wins.

## 3. Backtest runner wiring

- [x] 3.1 Move `signal_ids` extraction from `signal_results` to **before** the `calculate_strategy_equity_curve` and `calculate_portfolio_holdings` calls in `run_backtest` (`backtest_runner.py`).
- [x] 3.2 In `run_backtest`, pass the extracted `signal_ids` into both `calculate_strategy_equity_curve` and `calculate_portfolio_holdings`.
- [x] 3.3 Update `fake_calculate_portfolio_holdings` in `test_backtest_runner.py:371-391` to accept `signal_ids=None` parameter.
- [x] 3.4 Update `fake_calculate_strategy_equity_curve` in `test_backtest_runner.py:352-369` to accept `signal_ids=None` parameter.
- [x] 3.5 Add a failing runner wiring test proving the ids extracted from generated results are passed unchanged to both holdings and equity-curve calculations before result persistence/linking.
- [x] 3.6 Add an integration regression test in one isolated database: run the same config twice without resetting; arrange for the second run to have a failed signal at a rebalance date where the first run succeeded; assert the second run carries only its own prior successful signal, while the first run's persisted curve `positions_json` and metrics remain unchanged and both runs keep disjoint linked signal ids.

## 4. Verification

- [x] 4.1 Run targeted portfolio-holdings, strategy-equity-curve, and backtest-runner tests, then the full Python suite.
- [x] 4.2 Run `ruff check`, `ruff format --check`, `mypy` via repo CI commands.
- [x] 4.3 Run `openspec validate scope-backtest-signals-by-run --strict` and `openspec status --change scope-backtest-signals-by-run --json`; confirm all artifacts complete and tasks checked only after verification passes.

## 1. Lock the Corrected Behavior with Failing Tests

- [x] 1.1 Add focused equity-curve tests proving that a 50/50 multi-asset state drifts after unequal returns and that the following interval consumes the drifted state instead of the original targets.
- [x] 1.2 Add a single-ETF full-allocation regression proving that continuous value accounting remains equivalent to direct compounding when no cross-asset weight drift is possible.
- [x] 1.3 Add rebalance-boundary tests proving that old actual holdings earn the interval ending on a new signal's effective date and the new target state earns only the following interval.
- [x] 1.4 Add a same-target/new-`strategy_signal_id` regression proving that drifted weights are recentered and incur non-zero turnover even when consecutive signals contain identical target maps.
- [x] 1.5 Update transaction-cost tests to assert turnover from pre-trade actual weights and multiplicative market-return/cost sequencing, including entry, exit, zero-cost, different-rate, and cost-exhaustion cases.
- [x] 1.6 Add edge-case tests for empty-to-cash state, missing-price value carry, three-way repeating Decimal targets, non-positive assets, and multi-day high-precision state that is not reconstructed from six-decimal outputs.
- [x] 1.7 Add runner tests asserting actual `cash`, `market_value`, `total_assets`, `target_weight`, `actual_weight`, and `equity_model_version: "drift_v1"` persistence, including a drifted non-rebalance date and explicit rejection of an equity point without calculated state.

## 2. Implement Continuous Portfolio-State Accounting

- [x] 2.1 Add immutable equity-point position/state representations needed to expose normalized cash, aggregate market value, signal target weights, and actual weights; attach them through one optional state payload so existing three-field metric-only `StrategyEquityCurvePoint` construction remains compatible, while calculator-produced points always populate the payload.
- [x] 2.2 Initialize the first point from its effective holding snapshot as a post-initialization `1.000000` baseline, with empty holdings represented as cash and no initial-point transaction cost.
- [x] 2.3 Normalize positive non-empty target weights at execution boundaries so repeating Decimal allocations consume the full portfolio without negative residual cash or phantom turnover.
- [x] 2.4 Replace daily target-weight return calculation with high-precision per-ETF normalized market values carried across intervals and marked through the existing per-interval `forward_adjusted_prices` contract.
- [x] 2.5 Preserve a held ETF's state with a neutral multiplier when either endpoint price is missing, and fail explicitly when non-positive assets prevent a meaningful weight calculation.
- [x] 2.6 Detect rebalances from `strategy_signal_id` transitions, calculate turnover over the union of pre-trade actual and new target ETFs, deduct cost from marked-to-market assets, and allocate the post-cost state to the new target.
- [x] 2.7 Keep internal Decimal state unquantized across dates and quantize only exposed values, reconciling output aggregates so `cash + market_value == total_assets == net_value`.
- [x] 2.8 Update core public exports and type annotations for any new equity-state value objects without changing the inputs to annualized-return, drawdown, volatility, or Sharpe calculations.

## 3. Persist the Authoritative Calculated State

- [x] 3.1 Change the backtest runner to map `BacktestEquityCurveInput` rows directly from the state carried by equity points instead of independently deriving account values and positions from target holding snapshots, and fail explicitly if a point lacks calculator-produced state.
- [x] 3.2 Preserve `etf_id` and `target_weight` in `positions_json`, add `actual_weight`, and serialize deterministic six-decimal values for invested, drifted, rebalanced, and cash-only points.
- [x] 3.3 Add `equity_model_version: "drift_v1"` to each new run's canonical runner-generated `parameters_json` and update exact runner/API fixtures that represent those generated runs; keep generic persistence/report fixtures capable of representing historical or caller-supplied parameter payloads.
- [x] 3.4 Remove only imports, duplicate holdings calculation, helpers, or fixtures made unused by the new single-source state flow; do not refactor unrelated runner or persistence code.

## 4. Verify Metrics and Orchestration

- [x] 4.1 Run `uv run pytest packages/core/tests/test_strategy_equity_curve.py` and confirm all drift, timing, cost, precision, and edge-case expectations pass.
- [x] 4.2 Run `uv run pytest packages/core/tests/test_backtest_runner.py packages/core/tests/test_backtest_result_persistence.py packages/core/tests/test_backtest_report.py` and confirm persisted state and model-version contracts pass.
- [x] 4.3 Run the relevant walk-forward runner/report tests and verify `top_n=1..3` candidate backtests all flow through the same `drift_v1` equity model without adding special-case walk-forward behavior.
- [x] 4.4 Run the complete core test suite plus repository Ruff format/lint and mypy gates, fixing only failures caused by this Change.
- [x] 4.5 Run a representative end-to-end backtest against an isolated temporary database and independently check at least one non-rebalance drift interval and one same-target or changed-target rebalance boundary; do not write to persistent `vela.db`.
- [x] 4.6 Run `openspec validate fix-portfolio-weight-drift --strict`, trace every delta-spec scenario to implementation and test evidence, and leave all historical backtest rows untouched.

## 1. Add market price panel loader

- [x] 1.1 Create `packages/core/src/vela_core/market_price_query.py` with public `load_price_panel(session, *, etf_ids, start_date, end_date) -> dict[int, list[MarketPrice]]`
- [x] 1.2 Export `load_price_panel` from `packages/core/src/vela_core/__init__.py`
- [x] 1.3 Add unit tests covering: single ETF range, multi-ETF range, empty list, ETF with zero rows in range, ordering ascending

## 2. Split compute from IO in trend filter, momentum, moving average

- [x] 2.1 In `trend_filter.py`, extract `_trend_filter_from_prices(prices: list[MarketPrice], config) -> TrendFilterResult`; rewrite `apply_trend_filter(session, ...)` to load via `load_price_panel` for one ETF then delegate to the pure function
- [x] 2.2 In `momentum_scoring.py`, extract `_momentum_score_from_prices(prices: list[MarketPrice], config) -> MomentumScore`; rewrite `calculate_momentum_score(session, ...)` to delegate through panel loading
- [x] 2.3 In `market_price_moving_average.py`, extract `_moving_average_from_prices(prices: list[MarketPrice], window) -> MarketPriceMovingAverage`; rewrite `calculate_market_price_moving_average(session, ...)` to delegate through panel loading
- [x] 2.4 Add deprecation note in old docstrings ("prefer the panel-driven pure function in signal generation")

## 3. Convert generate_strategy_signal to a pure function

- [x] 3.1 Rewrite `generate_strategy_signal` to take `*, signal_date, config, price_panel, active_etfs, defense_lookup, generated_at=None, persist=None`; remove `session` parameter
- [x] 3.2 Replace per-ETF `apply_trend_filter` / `calculate_momentum_score` calls with in-memory `_trend_filter_from_prices` / `_momentum_score_from_prices` using the injected panel slice
- [x] 3.3 Resolve defensive asset id from `defense_lookup` dict instead of querying `ETFInfo`
- [x] 3.4 Invoke optional `persist` callback with the generated result instead of writing through `persist_strategy_signal` directly; produce a failed result without raising when the active list is empty or defense lookup misses

## 4. Convert generate_historical_strategy_signals to accept injected panel

- [x] 4.1 Rewrite `generate_historical_strategy_signals(rebalance_dates, *, config, price_panel, active_etfs, defense_lookup, persist=None)` to remove the session parameter and the panel-loading responsibility
- [x] 4.2 Confirm the function issues zero `MarketPrice` queries by inspection and by a query-counting test

## 5. Adapt CLI and API call sites to the new pure-function entry point

- [x] 5.1 In `apps/cli/src/vela_cli/main.py`, update `signal generate` to: load active ETFs, build `defense_lookup`, call `load_price_panel` once for `end_date=signal_date`, call `generate_strategy_signal(..., persist=lambda r: persist_strategy_signal(session, ...))`
- [x] 5.2 In `apps/api/src/vela_api/main.py`, update the `POST /api/strategy-signals/generate` handler with the same three-step pattern
- [x] 5.3 Verify both paths still surface the same `GenerateStrategySignalResult` fields

## 6. Load the panel once in run_backtest

- [x] 6.1 In `run_backtest`, before calling `generate_historical_strategy_signals`, call `load_price_panel` with the full active ETF id list and a window that starts at `rebalance_dates[0] - max(long_window, ma_window) - 5 calendar days`
- [x] 6.2 Pass the loaded panel plus `active_etfs` and `defense_lookup` into `generate_historical_strategy_signals`
- [x] 6.3 Confirm that `BacktestRunResult` is unchanged in shape and that the resulting `StrategySignal` rows match the pre-change backtest for an identical fixture

## 7. Refresh existing tests for the pure-function API

- [x] 7.1 Update `packages/core/tests/test_strategy_signal_generation.py` to build a fixture `price_panel` and `active_etfs` / `defense_lookup` and call the new pure-function signature
- [x] 7.2 Update tests covering `apply_trend_filter`, `calculate_momentum_score`, `calculate_market_price_moving_average` to assert behavior of the pure functions independently of database I/O
- [x] 7.3 Add a query-counting test that monkey-patches `session.scalar` / `session.scalars` and asserts: a single signal generates zero `MarketPrice` queries; one full backtest generates at most one `MarketPrice` query for the panel plus the existing non-`MarketPrice` reads

## 8. End-to-end regression

- [x] 8.1 Run `uv run pytest` and ensure all tests pass
- [x] 8.2 Run `uv run vela backtest run --strategy-config config/strategy_v1.yaml --start-date <T-5y> --end-date <today>` and diff the persisted `StrategySignal` rows against the same run executed on the pre-change commit (byte-equivalent on `signal_date / result / positions[etf_id, rank, score, target_weight]`)
- [x] 8.3 Run `uv run vela signal generate --date <today>` once and confirm the CLI exits with the expected status and the dashboard reads the new signal
- [x] 8.4 Update `openspec/changes/.../proposal.md` and `tasks.md` checkboxes; archive the change via `openspec archive`
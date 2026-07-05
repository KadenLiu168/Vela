## 1. Monthly rebalance date generator

- [ ] 1.1 In `packages/core/src/vela_core/rebalance_dates.py`, add `generate_monthly_rebalance_dates(trading_dates)` mirroring `generate_weekly_rebalance_dates` but grouping by `(year, month)` and taking the last available trading date per month.
- [ ] 1.2 In the same file, add internal dispatcher `generate_rebalance_dates(trading_dates, *, frequency)` with `Literal["weekly", "monthly"]` that routes to the two concrete functions.

## 2. Rebalance configuration schema

- [ ] 2.1 In `packages/core/src/vela_core/strategy_config.py`, add a `RebalanceConfig` Pydantic model with `frequency: Literal["weekly", "monthly"] = "weekly"`.
- [ ] 2.2 Add `rebalance: RebalanceConfig` to `StrategyConfig` so existing YAML without a `rebalance` section still loads with the default.
- [ ] 2.3 Add `rebalance: { frequency: weekly }` block to `config/strategy_v1.yaml` for explicitness.

## 3. Wire dispatcher into signal generation

- [ ] 3.1 In `packages/core/src/vela_core/strategy_signal_generation.py`, replace the direct `generate_weekly_rebalance_dates(historical_trading_dates)` call inside `generate_historical_strategy_signals` with `generate_rebalance_dates(historical_trading_dates, frequency=config.rebalance.frequency)`.
- [ ] 3.2 In `packages/core/src/vela_core/__init__.py`, export `generate_monthly_rebalance_dates` and `generate_rebalance_dates`.

## 4. Tests for monthly generator and dispatcher

- [ ] 4.1 In `packages/core/tests/test_rebalance_dates.py`, add tests for `generate_monthly_rebalance_dates` covering: last trading date per calendar month, holiday / missing-date preservation, cross-calendar-year grouping (December + January), deduplication, sort order, empty input.
- [ ] 4.2 In `packages/core/tests/test_rebalance_dates.py`, add tests for the dispatcher verifying that `frequency="weekly"` and `frequency="monthly"` route to the correct concrete functions, and that an unsupported frequency raises.
- [ ] 4.3 In `packages/core/tests/test_strategy_config.py` (or the equivalent test file for `StrategyConfig`), add tests for `RebalanceConfig` covering: default value is `weekly`, both `weekly` and `monthly` are accepted, unsupported values are rejected.
- [ ] 4.4 In `packages/core/tests/test_strategy_signal_generation.py`, add a test asserting that with the same trading-date input, `monthly` frequency produces strictly fewer persisted signals than `weekly`, and that the persisted `signal_date` values lie on calendar month ends.

## 5. Verification

- [ ] 5.1 Run `uv run pytest packages/core/tests/test_rebalance_dates.py packages/core/tests/test_strategy_config.py packages/core/tests/test_strategy_signal_generation.py` and confirm all green.
- [ ] 5.2 Run the full `uv run pytest` suite to confirm no regressions in the rest of the test suite (backtest, CLI, API).
- [ ] 5.3 Run `uv run ruff check` and `uv run ruff format --check` to confirm lint/format compliance on the modified files.
- [ ] 5.4 Run `uv run mypy packages/core/src/vela_core/rebalance_dates.py packages/core/src/vela_core/strategy_config.py packages/core/src/vela_core/strategy_signal_generation.py` and confirm no new type errors.

## 1. Strategy Configuration

- [x] 1.1 Add `trend_filter` to `config/strategy_v1.yaml` with `moving_average_days: 120` and `price_relation: above`.
- [x] 1.2 Add a frozen trend filter config model to `StrategyConfig` that accepts only the v1-supported 120-day moving average and `above` relation.
- [x] 1.3 Update strategy configuration tests for the checked-in config, missing required groups, and unsupported trend filter values.

## 2. Trend Filter Tests

- [x] 2.1 Add a unit test where current strategy price is greater than the 120-day moving average and the ETF passes.
- [x] 2.2 Add unit tests where current strategy price equals or is less than the 120-day moving average and the ETF fails.
- [x] 2.3 Add a unit test where the current price is missing and the ETF fails with null current price.
- [x] 2.4 Add a unit test where fewer than 120 same-ETF price rows exist and the ETF fails with null moving average.
- [x] 2.5 Add a unit test proving other ETF histories do not affect the current price or moving average.

## 3. Core Implementation

- [x] 3.1 Add a frozen trend filter result dataclass with ETF id, as-of date, current price, moving average, and pass/fail status.
- [x] 3.2 Implement a trend filter function that accepts a SQLAlchemy session, ETF id, as-of date, and `StrategyConfig`.
- [x] 3.3 Query only the requested ETF's current `MarketPrice` row for `as_of_date` and use `MarketPrice.strategy_price`.
- [x] 3.4 Reuse `calculate_market_price_moving_average` for the configured 120-day moving average.
- [x] 3.5 Return `passes_filter=True` only when current strategy price and moving average both exist and `current_price > moving_average`.
- [x] 3.6 Export the trend filter result type and function from `vela_core`.

## 4. Verification

- [x] 4.1 Run focused strategy configuration and trend filter unit tests.
- [x] 4.2 Run existing moving-average tests to confirm behavior was not regressed.
- [x] 4.3 Run `openspec status --change "apply-trend-filter"` and confirm the change is apply-ready.

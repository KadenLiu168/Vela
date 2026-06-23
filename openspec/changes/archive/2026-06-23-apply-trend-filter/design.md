## Context

Vela already stores ETF daily market prices, exposes `MarketPrice.strategy_price`, and calculates a 120-trading-day moving average for one ETF. The v1 rotation strategy now needs a trend gate so later signal generation can exclude candidates whose current strategy price is not above their moving average before momentum ranking.

## Goals / Non-Goals

**Goals:**
- Represent the v1 trend filter in `StrategyConfig` and `config/strategy_v1.yaml`.
- Apply the trend filter for one ETF and one `as_of_date`.
- Reuse the existing 120-day moving-average calculation instead of duplicating average logic.
- Return current price, moving average, and pass/fail status for diagnostics.
- Cover passing, failing, missing-data, and ETF-isolation cases with unit tests.

**Non-Goals:**
- Do not implement ETF ranking, Top N selection, defensive fallback, signal persistence, or backtesting.
- Do not add arbitrary trend-filter operators or moving-average windows beyond the v1 contract.
- Do not change market price persistence, moving-average semantics, or provider ingestion.

## Decisions

1. Add a narrow `trend_filter` strategy config group.

   Rationale: the acceptance criteria require filtering logic to match configuration, and checked-in strategy config should expose the rule used by signal generation. Keep the v1 schema small with `moving_average_days` fixed to `120` and `price_relation` fixed to `above`.

   Alternative considered: hard-code the rule in the filtering function. That would be simpler initially, but it would make the configured strategy incomplete and harder to audit.

2. Use strict `current_price > ma_120d` for `above`.

   Rationale: "above" should mean strictly above the moving average. Treating equality as passing would make the rule less explicit and broaden the filter without a configured reason.

   Alternative considered: support `at_or_above`. That can be added later if a strategy requires it, but it is not needed for v1.

3. Implement trend filtering as a separate core module.

   Rationale: trend filtering is strategy logic that composes current price lookup with the existing moving-average API. A small module keeps ORM models and market-data helpers focused on their current responsibilities.

   Alternative considered: expand `market_price_moving_average` to return pass/fail. That would mix a strategy rule into a market-data calculation primitive.

4. Fail closed on missing data.

   Rationale: missing current price or missing moving average means the system cannot prove the ETF is in an uptrend. Returning `passes_filter=False` keeps later ranking deterministic and avoids accidental inclusion.

   Alternative considered: return a tri-state status. That may be useful for reporting later, but the first filter API only needs a boolean plus diagnostic values.

## Risks / Trade-offs

- Config schema is intentionally narrow -> Mitigation: use `Literal` validation so unsupported windows or relations fail clearly.
- Current price lookup and moving-average calculation perform separate queries -> Mitigation: keep the first implementation simple and tested; optimize later only if batch signal generation needs it.
- Missing data is collapsed into `passes_filter=False` -> Mitigation: return `current_price` and `moving_average` diagnostics so callers can distinguish why the ETF failed.

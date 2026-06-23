## Context

Vela already stores daily ETF prices in `MarketPrice` and defines `MarketPrice.strategy_price` as adjusted close when available, otherwise close price. The core package also has a tested window-return module that calculates 20 / 60 / 120 trading-day returns from the same data shape.

The MA120 calculation should follow that existing pattern: a small backend API that reads same-ETF price history for one `as_of_date` and returns a typed result for later strategy filtering.

## Goals / Non-Goals

**Goals:**
- Provide a tested 120-trading-day moving average for one ETF and one `as_of_date`.
- Reuse `MarketPrice.strategy_price` so moving average and other strategy metrics share the same price-selection rule.
- Return a nullable MA120 value instead of raising when required history is unavailable.

**Non-Goals:**
- Do not implement strategy signal generation or trend-filter decisions.
- Do not add database columns, migrations, market data ingestion changes, or provider changes.
- Do not generalize to arbitrary moving-average windows until a concrete caller needs it.

## Decisions

1. Add a dedicated moving-average module in `packages/core`.

   Rationale: this matches the existing `market_price_returns.py` shape and keeps multi-row query logic out of ORM row models.

   Alternative considered: extend `MarketPriceReturns`. That would mix return and average semantics and make the API less clear for trend filtering.

2. Return a frozen dataclass with `etf_id`, `as_of_date`, and `ma_120d`.

   Rationale: callers get a stable typed result even when the MA120 cannot be calculated. `None` on `ma_120d` represents insufficient or missing current data.

   Alternative considered: return only `Decimal | None`. That is smaller, but loses useful context and diverges from the existing return-calculation API.

3. Count the window by trading price rows and include the `as_of_date` row.

   Rationale: trading-row counting avoids ambiguity around weekends, holidays, and incomplete provider histories. Including the current row matches common daily moving-average usage after close.

   Alternative considered: use 120 calendar days or only prior rows. Calendar days would be inconsistent with existing return windows, and prior-only windows are more appropriate for intraday signals, which are out of scope.

4. Use `MarketPrice.strategy_price` for each row in the average.

   Rationale: market-data already defines the strategy price selection rule, and existing strategy metrics use it.

   Alternative considered: always use raw `close_price`. That matches the literal field name but would create inconsistent strategy inputs when adjusted close is available.

## Risks / Trade-offs

- Future strategies may need multiple MA windows -> Add only MA120 now; introduce a configurable helper when there is a real second caller.
- Current-day prices may be unavailable before daily fetch completes -> Return `ma_120d=None` so callers can skip trend filtering or mark the ETF unavailable.
- Database histories may contain gaps -> Treat available rows as trading observations, matching existing return-window behavior.

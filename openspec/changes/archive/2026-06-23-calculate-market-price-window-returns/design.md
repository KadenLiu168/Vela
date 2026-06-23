## Context

Vela already stores daily ETF prices in `MarketPrice` and defines `MarketPrice.strategy_price` as adjusted close when available, otherwise close price. The strategy configuration currently has momentum parameters, but there is no reusable, tested calculation that turns stored price history into the 20 / 60 / 120 trading-day returns needed for signal generation.

## Goals / Non-Goals

**Goals:**

- Provide a small core API that calculates 20 / 60 / 120 trading-day returns for one ETF and one `as_of_date`.
- Reuse `MarketPrice.strategy_price` so strategy price selection remains centralized.
- Make missing current or historical data explicit with `None` window values.
- Keep the calculation easy to test without adding schema or dependency complexity.

**Non-Goals:**

- Do not implement full strategy signal generation or ranking.
- Do not persist calculated returns in the database.
- Do not change market data ingestion, upsert behavior, or `MarketPrice` schema.
- Do not replace existing `strategy_v1.yaml` momentum windows.

## Decisions

1. Add a dedicated core calculation module.

   The implementation should live in a small module such as `vela_core.market_price_returns`, with a public function like `calculate_market_price_returns(session, *, etf_id, as_of_date)`. This keeps business logic in `packages/core` and avoids mixing return calculation into the ORM model or CLI entrypoints.

   Alternative considered: add methods to `MarketPrice`. That would put query logic on an ORM row and make multi-row history calculations less clear.

2. Return a typed result object with nullable window values.

   Use a frozen dataclass containing `etf_id`, `as_of_date`, `return_20d`, `return_60d`, and `return_120d`. A missing current price or insufficient history should not raise; only the affected return values should be `None`.

   Alternative considered: skip ETFs or raise errors on missing history. That is stricter, but it hides partial diagnostics or makes normal early-history datasets fail.

3. Count windows by stored trading price rows.

   The 20-day return should compare the current row to the 20th earlier `MarketPrice` row for the same ETF ordered by `trade_date`; 60 and 120 use the same rule. This avoids calendar-day ambiguity around weekends, holidays, and incomplete provider histories.

   Alternative considered: subtract calendar days from `as_of_date`. That would require extra rules for non-trading days and missing dates.

4. Query only the required ETF history up to `as_of_date`.

   The implementation can load the requested ETF's prices with `trade_date <= as_of_date`, ordered descending or ascending, and use at most the current row plus 120 prior rows. It should not scan or count prices from other ETFs.

   Alternative considered: calculate all ETFs in one batch. That may be useful for future signal generation, but the first API is simpler and composable.

## Risks / Trade-offs

- Exact `as_of_date` requirement may produce all `None` on non-trading dates -> callers should pass a known trading date or add a separate latest-prior-date lookup later.
- Row-count windows depend on local data completeness -> tests should cover insufficient history, and future ingestion diagnostics can surface missing market data.
- Decimal precision follows stored `Numeric` values and Python `Decimal` division -> tests should assert exact values for simple inputs and avoid over-rounding in the calculation.

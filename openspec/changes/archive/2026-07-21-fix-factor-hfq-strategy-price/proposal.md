## Why

`MarketPrice.strategy_price` (close × factor_hfq) is the pricing source for momentum scoring, trend filtering, equity-curve returns, market-price returns/moving averages, and the ETF trend endpoint. The backward-adjustment factor `factor_hfq` is excluded from the upsert conflict SET — so when a corporate action triggers a full refetch, historical rows silently retain old factors while new rows receive recalculated ones. The resulting cross-batch factor anchor inconsistency produces false price jumps at boundary dates, silently corrupting downstream ratio-based calculations. A correct forward-adjusted pricing function (`forward_adjusted_prices`) already exists and has passing tests but is dead code — zero production callers.

## What Changes

- **BREAKING (persistence behavior)**: Include `factor_hfq` in the upsert `ON CONFLICT DO UPDATE SET` clause. Existing rows' backward-adjustment factors are now updated when refetched, eliminating cross-batch anchor inconsistency at the data layer.
- All signal, trend, returns, trend-chart, and backtesting consumers switch from directly accessing `MarketPrice.strategy_price` to computing normalized prices via `forward_adjusted_prices()` — a pure function that normalizes the factor-adjusted series against a rebalance-date anchor. Equity-curve daily returns normalize the two prices of each close-to-close interval at that interval's current date; other consumers normalize their whole as-of window at `as_of_date`.
- **BREAKING (Python API)**: Remove the `MarketPrice.strategy_price` property from the ORM model. Pricing logic moves out of the persistence layer into the dedicated `adjusted_price_projection` module.
- **Response-shape-compatible numeric correction**: The ETF trend endpoint keeps its URL and JSON shape, but its `price` values become forward-adjusted and are anchored at the latest date in the selected range; the final point therefore equals that day's unadjusted close rather than a backward-adjusted scale. The frontend chart only updates its accessible label; it continues to render returned values without additional adjustment.

## Capabilities

### New Capabilities

None. This is a correctness fix; no new business capabilities are introduced.

### Modified Capabilities

- `market-data`: The `upsert_market_prices` function no longer treats `factor_hfq` as append-only. On conflict, `factor_hfq` is updated alongside open/high/low/close/volume, ensuring all rows for a given ETF share a consistent factor anchoring base after corporate action refetches.
- `adjusted-price-projection`: Elevated from dead code to the canonical normalized pricing source. All consumers that previously relied on `MarketPrice.strategy_price` must compute prices through `forward_adjusted_prices()` anchored at their rebalance date. The `MarketPrice.strategy_price` property is removed.
- `etf-price-trend`: Keep the endpoint and response shape but define its price points as forward-adjusted, anchored at the latest date in the selected range.

## Impact

- **Data layer**: `packages/core/src/vela_core/market_price_upsert.py` — add `factor_hfq` to conflict SET
- **Model layer**: `packages/core/src/vela_core/models/market_price.py` — remove `strategy_price` property
- **Consumers** (all files using `strategy_price`):
  - `packages/core/src/vela_core/momentum_scoring.py`
  - `packages/core/src/vela_core/trend_filter.py`
  - `packages/core/src/vela_core/strategy_equity_curve.py`
  - `packages/core/src/vela_core/market_price_returns.py`
  - `packages/core/src/vela_core/market_price_moving_average.py`
  - `packages/core/src/vela_core/etf_price_trend.py`
- **Activated module**: `packages/core/src/vela_core/adjusted_price_projection.py` — already implemented with passing tests, needs no code changes
- **Frontend semantics**: `apps/web/src/pages/EtfDetailPage.tsx` — rename the chart's accessible title from backward-adjusted to forward-adjusted; no geometry or numeric transformation changes
- **Tests**: Cover factor overwrite through both direct upsert and the corporate-action full-refetch path; cover every consumer with non-uniform factors, including the core and HTTP ETF-trend contracts and an equity-curve interval crossing a factor change.
- **Existing local data**: After release, run the existing full fetch command (`uv run vela fetch-market-data`, without `--incremental`) against a recoverable copy of each retained database and require a `success` result with no failed symbols. A `partial` result commits repairs for successful active ETFs only and is not completion; rerun after resolving provider failures. Full fetch only includes active ETFs, so inactive historical rows are not automatically repaired. No Alembic migration is required.
- **Persisted research results**: Existing `StrategySignal` and `BacktestRun` records are historical outputs and are not rewritten. After the full fetch, operators decide which reports/backtests need an explicit rerun; automatic mutation of historical records is out of scope.

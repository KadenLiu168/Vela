## Why

Vela can already generate strategy signals and run backtests, but a researcher has no way to
visually inspect a single ETF's historical price trend. ETF rotation decisions are momentum-driven,
and judging a candidate ETF requires seeing its backward-adjusted price trajectory over multiple
horizons. The Dashboard already lists every active ETF (`etf_list`), yet each row offers no entry
point into that ETF's history. This change adds a single-ETF price-trend view, addressable from the
Dashboard, so a researcher can confirm a holding candidate's trajectory before trusting a signal.

## What Changes

- Add backend endpoint `GET /api/etfs/{etf_id}/prices?range={1m|3m|1y|3y|max}` returning the ETF's
  backward-adjusted daily price series over the requested horizon. The series reuses the stored
  `factor_hfq` (no new persistence, no new migration); each point is `trade_date` + `price` where
  `price = close_price * factor_hfq`.
- Add web route `/etfs/{etf_id}` (ETF trend detail page) with a horizon switcher
  (`1M / 3M / 1Y / 3Y / Max`) and a hand-written SVG trend line chart with hover readout
  (date + price) and axis labels. Horizon switching changes the displayed time window only; the
  underlying data stays daily-resolution (no resampling/aggregation).
- Extend the Dashboard aggregate `etf_list` so each entry carries `etf_id`, and render a detail
  entry control on each Dashboard `etf-row` that navigates to `/etfs/{etf_id}`.
- Price viewpoint is the backward-adjusted `strategy_price`, consistent with the
  `adjusted-price-projection` capability, so ex-dividend dates do not produce artificial jumps.

## Capabilities

### New Capabilities

- `etf-price-trend`: End-to-end single-ETF price-trend viewing — the `GET /api/etfs/{id}/prices`
  endpoint contract (horizon resolution, backward-adjusted price derivation, 404/error behavior),
  the `/etfs/{id}` web page behavior (horizon switching, loading/empty/error states), and the trend
  chart interaction contract (hover readout, axis labeling, single-point handling).

### Modified Capabilities

- `dashboard-aggregation`: The Dashboard `etf_list` entries SHALL include `etf_id` so each ETF row
  can link to its trend detail page.

## Impact

- `packages/core`: Dashboard aggregation service returns `etf_id` per `etf_list` entry; add a
  single-ETF backward-adjusted price-series query helper (built on the existing
  `ix_market_price_etf_trade_date` index / `load_price_panel` pattern).
- `apps/api`: New `GET /api/etfs/{etf_id}/prices` handler with `range` query param; Dashboard
  handler forwards `etf_id` through the aggregate response.
- `apps/web`: New `EtfDetailPage`, trend-chart component (hand-written SVG), API client method +
  response type, `/etfs/:id` route in `App.tsx`; `DashboardPage` `etf-row` gains a detail entry
  control; `DashboardResponse` type gains `etf_id`.
- Dependencies: none added (chart is hand-written SVG, consistent with the existing
  `BacktestDetailPage` equity-curve chart).
- Database: no migration; reuses `market_price.close_price` + `market_price.factor_hfq`.

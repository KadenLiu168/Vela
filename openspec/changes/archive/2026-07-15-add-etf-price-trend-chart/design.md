## Context

Vela stores daily ETF market prices in `market_price` (OHLCV + `factor_hfq`), loaded for multiple
ETFs via `load_price_panel` (single SELECT over `ix_market_price_etf_trade_date`). The
`adjusted-price-projection` capability already establishes the backward-adjusted
`strategy_price = close_price * factor_hfq` as the dividend-correct viewpoint used for net value /
equity curves, computed at query time without persistence. The web frontend has one existing chart:
the `BacktestDetailPage` equity curve is a hand-written SVG line (no hover, no axis labels), and the
project carries zero chart-library dependencies. The Dashboard aggregate `etf_list` currently exposes
`exchange / symbol / name / category / earliest_trade_date` per ETF but no `etf_id`, so no row can
link to a per-ETF view. There is no ETF detail page today.

## Goals / Non-Goals

**Goals:**

- Single-ETF backward-adjusted daily price trend, viewable over `1M / 3M / 1Y / 3Y / Max` horizons.
- Hand-written SVG trend chart with hover readout (date + price) and axis labels.
- Dashboard `etf-row` links into the per-ETF trend detail page.
- No new runtime dependency, no database migration.

**Non-Goals:**

- No resampling to weekly/monthly/yearly bars - `range` changes the time window only; data stays
  daily-resolution.
- No candlestick / multi-ETF overlay / technical indicators (MA, BOLL). If those land later, that is
  the trigger to introduce a chart library.
- No standalone ETF list page - only the detail page, entered from the Dashboard.
- No real-time or push updates - reads persisted `market_price` rows only.

## Decisions

### D1: `range` is a time window, not a resample

Selected: option B - keep daily precision, `range` only narrows the `start_date`/`end_date` filter.
Alternative A (resample to weekly/monthly/yearly bars, one point per bucket) was rejected: it requires
backend `GROUP BY` aggregation, and for an ETF rotation strategy whose momentum windows are 60/120/250
trading days, weekly bars carry no useful information. B matches mainstream financial UIs (Yahoo
Finance, Xueqiu, TradingView range buttons) and reuses `load_price_panel`'s date-range filtering.

### D2: Price viewpoint is backward-adjusted `strategy_price`

`price = close_price * factor_hfq`, computed at query time, never persisted. This reuses the
`adjusted-price-projection` contract already used for net value / equity curves, so ex-dividend dates
do not produce artificial jumps in the trend. Unadjusted close was rejected (false drops on
ex-dividend); forward-adjusted was rejected because it requires a rebalance-date anchor to normalize
against, which a trend view has no notion of.

### D3: Hand-written SVG chart, no library

Extend the existing `BacktestDetailPage` SVG-line pattern with hover + axis labels. Alternative
recharts was rejected: it adds ~45kb gzip, requires a `design-system` token -> theme mapping layer,
and creates a split "two chart implementations" cognitive load. Single-series line is the simplest
chart; hand-written keeps full control and uses `var(--*)` tokens with zero glue, consistent with
every existing chart in the project. Boundary: candlestick / multi-series / indicators would justify
a library - explicitly out of scope here.

### D4: Horizon preset is `1M / 3M / 1Y / 3Y / Max`

"Week" is excluded: one week is five trading days, which carries no trend information for a rotation
strategy. `1M / 3M / 1Y / 3Y / Max` covers short / medium / long / full-history and aligns with
mainstream financial UIs. `Max` uses the ETF's own `earliest_trade_date` as the lower bound.

### D5: Route `/etfs/{etf_id}`, Dashboard gains `etf_id` (option b)

Mirrors existing `/signals/{id}` and `/backtests/{id}` routing, keeping URLs short and
uncoded. Alternative a (`/etfs/{exchange}:{symbol}`) avoids a backend change but requires URL-encoding
the colon and is less readable. `dashboard-aggregation` adds `etf_id` per `etf_list` entry - a small
change since `ETFInfo.id` already exists.

### D6: `range` -> `start_date` resolution

- `1m / 3m / 1y / 3y`: `start_date = latest_trade_date(of this ETF) - N calendar months/years`;
  `end_date = latest_trade_date(of this ETF)`.
- `max`: no lower bound.
- The window end is the ETF's latest persisted `trade_date`, not `today`, so weekend/holiday tails do
  not produce empty segments. A `start_date` landing on a non-trading day is harmless - the DB filter
  (`trade_date >= start_date`) naturally yields the next trading day.

## Risks / Trade-offs

- [Range spanning a data gap] An ETF with a long outage (suspension / un-fetched span) shows as a
  slope change between adjacent points; no interpolation. -> Acceptable; the hover readout and the
  Dashboard coverage dates make the gap legible. Document, do not interpolate.
- [Max horizon point count] An old ETF may carry thousands of daily points; rendering all of them in
  SVG can degrade responsiveness. -> Phase 1 is a personal-research workload with bounded data; if a
  series exceeds a threshold (~2000 points), core-layer down-sampling (stride or LTTB) is the escape
  hatch. Explicitly deferred this change - left as a note, not implemented now.
- [Hand-written hover complexity] Hover requires manual nearest-point hit-testing, tooltip
  positioning, and responsive mapping. -> Constrain to a fixed viewBox with CSS scaling; map pointer
  events to a data index. Reuse the coordinate-builder pattern from the equity-curve chart.
- [Sequential `etf_id` in URL] `/etfs/{id}` exposes the auto-increment id. -> Acceptable for a
  personal-research tool; no auth is in scope.

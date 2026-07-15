## 1. Backend core: trend query & dashboard etf_id

- [x] 1.1 Add `get_etf_price_trend(session, etf_id, range)` to `packages/core` returning an `EtfPriceTrendResult` (ETF identity `id/exchange/symbol/name` + `points` list of `(trade_date, price)` where `price = close_price * factor_hfq`); resolve `range` (`1m|3m|1y|3y|max`) to a date window anchored at the ETF's latest persisted `trade_date` per design D6; return empty `points` when the ETF exists but has no prices; return a distinct not-found signal when no `ETFInfo` row exists
- [x] 1.2 Add core unit tests covering: 1y/3m/max windowing, backward-adjusted price value, empty-points case, unknown-etf not-found case
- [x] 1.3 Modify the dashboard aggregation service so each `etf_list` entry includes `etf_id`; update existing dashboard aggregation tests

## 2. Backend API: trend endpoint & dashboard passthrough

- [x] 2.1 Add `GET /api/etfs/{etf_id}/prices` handler with a `range` query enum (`1m|3m|1y|3y|max`, default `1y`) delegating to `get_etf_price_trend`; map unknown etf to 404 (`not_found`) and rely on FastAPI enum validation for 422 (`validation`) on invalid range
- [x] 2.2 Update the `/api/dashboard` handler to forward `etf_id` per `etf_list` entry
- [x] 2.3 Add API tests covering: 200 series shape + ordering, 404 unknown etf, empty points for existing etf, invalid range 422, range windowing

## 3. Frontend: API client & routing

- [x] 3.1 Add `EtfPriceTrendResponse` / `EtfPriceTrendPoint` types and `getEtfPriceTrend(etfId, range)` to `apps/web/src/api/client.ts`; add `etf_id` to the Dashboard `etf_list` entry type
- [x] 3.2 Add a `/etfs/:id` branch to `renderRoute` and `getActivePath` in `App.tsx`

## 4. Frontend: trend page & chart

- [x] 4.1 Create `apps/web/src/pages/EtfDetailPage.tsx` with a horizon switcher (`1M / 3M / 1Y / 3Y / Max`, default `1Y`), default-horizon fetch on mount, re-fetch on horizon change, and loading / not-found / error states consistent with `BacktestDetailPage`
- [x] 4.2 Create a hand-written SVG `TrendChart` component: line path, date-axis and price-axis labels, hover nearest-point readout (date + price), single-point state, empty state
- [x] 4.3 Add trend-page and chart unit tests (render with multi-point series, hover readout, single-point, empty, not-found)
- [x] 4.4 Add CSS for the trend page and chart to `apps/web/src/styles.css` using only `var(--*)` tokens; verify no `:root` block and `design-system` compliance via `npm --prefix apps/web run lint:css`

## 5. Frontend: Dashboard entry control

- [x] 5.1 Add a detail entry control to each Dashboard `etf-row` that navigates to `/etfs/{etf_id}`; render the control only when `etf_id` is present
- [x] 5.2 Add a Dashboard test asserting the `etf-row` entry control navigates to `/etfs/{etf_id}`

## 6. Validation

- [x] 6.1 Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`
- [x] 6.2 Run `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run lint`, `npm --prefix apps/web run test`, `npm --prefix apps/web run lint:css`
- [x] 6.3 Run `openspec status --change "add-etf-price-trend-chart"` and `openspec validate add-etf-price-trend-chart --strict` to confirm all artifacts apply-ready

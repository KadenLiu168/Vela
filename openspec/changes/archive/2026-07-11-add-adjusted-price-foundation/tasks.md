## 1. Database Migration

- [x] 1.1 Create Alembic migration to drop `adjusted_close` column and add `factor_hfq Numeric(18,12) NOT NULL` column on `market_price`
- [x] 1.2 Verify migration up/down works against a fresh SQLite database (`apps/api/tests/test_database_migrations.py` or equivalent)

## 2. Provider Layer (factor exposure)

- [x] 2.1 Add `factor: Decimal` field to `DailyPrice` dataclass in `market_data_provider.py`
- [x] 2.2 Update `base_market_data_provider._extract_row` to accept and populate `factor` (remove hardcoded `adjusted_close=None`)
- [x] 2.3 Update `JoinQuantMarketDataProvider._fetch_rows` to call `get_price(fq=None, fields=[..., "factor"])` so unadjusted OHLC and the raw backward-adjustment factor are returned together, and pass factor through normalization
- [x] 2.4 Update `AkShareMarketDataProvider` and `TencentMarketDataProvider` to fetch both unadjusted (`adjust=""`) and backward-adjusted (`adjust="hfq"`) data, derive `factor = backward_adjusted_close / unadjusted_close` per row, and pass through
- [x] 2.5 Update provider tests: mock backward-adjusted + factor returns, assert non-null `factor` on every `DailyPrice` (akshare/tencent/joinquant provider test files)

## 3. Storage & Mapping Layer

- [x] 3.1 Update `models/market_price.py`: remove `adjusted_close`, add `factor_hfq Numeric(18,12) NOT NULL`; change `strategy_price` property to `return self.close_price * self.factor_hfq`
- [x] 3.2 Update `market_price_mapping.to_market_price` to map `daily_price.factor` -> `MarketPrice.factor_hfq`
- [x] 3.3 Update `market_price_upsert.py` to upsert `factor_hfq` (replace `adjusted_close` in conflict/excluded sets)
- [x] 3.4 Update model/mapping/upsert tests: assert `factor_hfq` persisted, `strategy_price == close * factor`, `adjusted_close` absent

## 4. Forward-Adjusted Price Projection

- [x] 4.1 Create `adjusted_price_projection.py` (or extend `market_price_query.py`) with a function computing forward-adjusted (qfq) price series for an ETF window anchored at rebalance date `T`: `qfq(D) = close(D)*factor(D) / (close(T)*factor(T))`
- [x] 4.2 Verify `qfq(T) == close_price(T)` (rebalance-date forward-adjusted equals unadjusted execution price)
- [x] 4.3 Add tests: forward-adjusted projection correctness, no persistence/caching, ratio-signal equivalence vs backward-adjusted

## 5. Incremental Fetch Consistency Check

- [x] 5.1 In `market_data_fetcher.py`, add consistency check on every incremental fetch: compare stored last-row `factor_hfq` against upstream same-date factor (joinquant `factor` field / akshare·tencent derived factor), relative tolerance (default 1e-6). Note: in plan B the append-only factor snapshot is immune to upstream retroactive factor revisions, so this check's sole purpose is detecting corporate actions to assign correct factors to new rows (incremental fetch only pulls unadjusted prices).
- [x] 5.2 On factor mismatch (corporate action detected), trigger full refetch for that ETF (earliest date -> today) and rewrite factor series as append-only; record a `quality_warnings` entry consistent with trading-day-gap/duplicate-trade-date detection
- [x] 5.3 Add tests: factor-match appends new rows, factor-mismatch triggers refetch, warning recorded, historical factor rows not modified

## 6. Signal & Net Value Wiring

- [x] 6.1 Confirm momentum_scoring / trend_filter / market_price_returns / market_price_moving_average continue to consume `strategy_price` (now backward-adjusted); adjust test fixtures to use `factor_hfq` instead of `adjusted_close`
- [x] 6.2 Confirm signal-generation / backtest-signal path continues to consume `strategy_price` (now backward-adjusted); ratio-signal equivalence (Decision 5) satisfies the forward-adjusted price contract without wiring the projection, which remains reserved for presentation/reconciliation
- [x] 6.3 Confirm the backtest path has no explicit trade-fill step (signals via `strategy_price`, net value via the backward-adjusted equity curve); the unadjusted-`close_price` execution-price contract is reserved for a future explicit fill-simulation feature
- [x] 6.4 Confirm `strategy_equity_curve` net value uses backward-adjusted `strategy_price` (option Y); update equity-curve tests with factor-based fixtures and verify no artificial jump on ex-dividend dates

## 7. Data Initialization (reset + full refetch)

- [ ] 7.1 Add a CLI / script path to reset `market_price` table and run full refetch for all active ETFs (earliest date -> today) with new factor-aware providers
- [ ] 7.2 Run reset + full refetch against real data source (joinquant primary); verify `factor_hfq` populated for all stored rows
- [ ] 7.3 (Optional, decide at deploy) clean stale `strategy_signal` / `backtest` records that were computed from incorrect unadjusted prices

## 8. Spec & Validation

- [x] 8.1 Run `openspec validate add-adjusted-price-foundation --strict` and resolve any spec format errors
- [x] 8.2 Run full test suite (`pytest`), ruff, mypy; resolve failures from price viewpoint changes
- [ ] 8.3 Spot-check: pick an ETF with a known historical dividend/split, confirm signal values are now continuous across the ex-date (no jump) and backtest net value has no artificial drop on ex-dividend date

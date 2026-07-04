## 1. Implementation: Tencent provider module

- [x] 1.1 Create `packages/core/src/vela_core/tencent_market_data_provider.py` with class `TencentMarketDataProvider` implementing `MarketDataProvider` Protocol
- [x] 1.2 Add `MarketDataProviderError` re-use from existing `akshare_market_data_provider` (or import the existing one if it's already top-level)
- [x] 1.3 Implement `to_tx_symbol(symbol: str) -> str` helper: `15*` → `sz*`, else → `sh*`
- [x] 1.4 Implement `_fetch_rows(symbol, request_start, request_end)` calling `akshare.stock_zh_a_hist_tx(symbol=tx_symbol, start_date=..., end_date=..., adjust="")`
- [x] 1.5 Implement `_normalize_rows(rows, symbol, request_start, request_end)` mapping `date → trade_date`, `open → open_price`, `high → high_price`, `low → low_price`, `close → close_price`, `volume=None`, `adjusted_close=None`, drop `amount`
- [x] 1.6 Implement row validation: missing required values, invalid date, non-finite / <=0 price, inconsistent OHLC relationship — matching existing `AkShareMarketDataProvider` validation style
- [x] 1.7 Wrap fetch and normalize failures in `MarketDataProviderError` with `tencent market data provider error symbol=... start_date=... end_date=...: ...` message format
- [x] 1.8 Add `name = "tencent"` class attribute
- [x] 1.9 Export `TencentMarketDataProvider` from `packages/core/src/vela_core/__init__.py`

## 2. Implementation: Switch default provider in CLI

- [x] 2.1 In `apps/cli/src/vela_cli/main.py`, import `TencentMarketDataProvider` from `vela_core`
- [x] 2.2 Update `fetch_full_market_data` to instantiate `TencentMarketDataProvider()` by default (instead of `AkShareMarketDataProvider()`)
- [x] 2.3 Update `fetch_incremental_market_data` to instantiate `TencentMarketDataProvider()` by default

## 3. Implementation: Switch default provider in HTTP API

- [x] 3.1 In `apps/api/src/vela_api/main.py`, import `TencentMarketDataProvider` from `vela_core`
- [x] 3.2 Update the provider factory function to return `TencentMarketDataProvider()` by default

## 4. Tests: Tencent provider unit tests

- [x] 4.1 Create `packages/core/tests/test_tencent_market_data_provider.py`
- [x] 4.2 Test `to_tx_symbol`: `159915` → `sz159915`, `510300` → `sh510300`, `511010` → `sh511010`
- [x] 4.3 Test `get_etf_daily_prices` normalizes OHLC fields, drops `amount`, sets `volume=None` and `adjusted_close=None`
- [x] 4.4 Test date bounds passed to AkShare as `YYYYMMDD` strings
- [x] 4.5 Test default `start_date` fallback to `20000101` when no start_date provided
- [x] 4.6 Test empty AkShare result returns empty sequence
- [x] 4.7 Test source errors wrapped in `MarketDataProviderError` with `tencent market data provider error` prefix and symbol/date context
- [x] 4.8 Test normalization errors wrapped in `MarketDataProviderError`
- [x] 4.9 Test row validation: missing date, invalid date, non-numeric price, negative price, OHLC inconsistency
- [x] 4.10 Test whole-result rejection: any one invalid row → no partial `DailyPrice` results

## 5. Tests: Update integration test fixture

- [x] 5.1 In `tests/integration_data.py`, add `TENCENT_DAILY_PRICE_SAMPLE` based on the `pasted-text.txt` `{"rc":0,"data":{...}}` shape (or a representative AkShare `stock_zh_a_hist_tx` return value)
- [x] 5.2 Update any test that asserts on default provider name (e.g. `source=akshare` → `source=tencent` in fetch log assertions)

## 6. Verification

- [x] 6.1 Run `pytest packages/core/tests/test_tencent_market_data_provider.py` — all green
- [x] 6.2 Run `pytest` full suite — all green, no regression on `test_akshare_market_data_provider.py`
- [x] 6.3 Run `uv run vela fetch-market-data --incremental` on the user's machine — should complete with `status: success` or `partial` (not `failed`), no `RemoteDisconnected`
- [x] 6.4 Query `vela.db`: `SELECT count(*) FROM market_price;` and `SELECT count(*) FROM data_fetch_log WHERE source='tencent';` to confirm rows inserted and fetch log records Tencent as source
- [x] 6.5 Run `uv run vela fetch-market-data` (full mode, no incremental) and confirm it does not raise `RemoteDisconnected`
- [x] 6.6 Run `uv run vela-api` and confirm startup succeeds with no import errors

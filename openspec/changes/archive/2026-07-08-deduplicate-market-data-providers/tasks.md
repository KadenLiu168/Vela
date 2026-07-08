## 1. Relocate provider error type

- [x] 1.1 Move `MarketDataProviderError` class definition from `packages/core/src/vela_core/akshare_market_data_provider.py` into `packages/core/src/vela_core/market_data_provider.py` (alongside `DailyPrice` and the `MarketDataProvider` Protocol)
- [x] 1.2 Update `packages/core/src/vela_core/__init__.py` to import `MarketDataProviderError` from `market_data_provider` instead of `akshare_market_data_provider`; verify the public name `vela_core.MarketDataProviderError` still resolves
- [x] 1.3 Remove the now-stale `MarketDataProviderError` import from `tencent_market_data_provider.py` (it currently imports from the AkShare module); have it import from `market_data_provider` instead
- [x] 1.4 Confirm `test_provider_contract_module_remains_source_library_independent` still passes (asserts contract module source contains neither `"akshare"` nor `"pandas"`)

## 2. Introduce BaseMarketDataProvider

- [x] 2.1 Create `packages/core/src/vela_core/base_market_data_provider.py` defining `BaseMarketDataProvider` with: `__init__(self, source=None)` storing `self._source` (lazy `import_module("akshare")` when `None`); class-attr hooks `name`, `_source_label`, `_column_map`; abstract `_fetch_rows(self, request_symbol, request_start, request_end)` decorated with `@retry`; `_format_request_symbol(self, symbol)` defaulting to passthrough; `_sort_prices(self, prices)` defaulting to `sorted(prices, key=lambda p: p.trade_date)`
- [x] 2.2 Move the shared row-parsing/validation helpers (`_parse_decimal`, `_parse_price`, `_parse_volume`, `_parse_trade_date`, `_validate_ohlc`, `_require_value`, `_is_missing`, `_format_date`, `_validation_error`, `_error_message`) into the base module as module-level functions, parameterized by `_source_label` for error messages
- [x] 2.3 Implement the final `get_etf_daily_prices` orchestration on the base (compute `request_start`/`request_end`, call `_format_request_symbol`, try `_fetch_rows` → wrap source errors, try `_normalize_rows` → wrap normalization errors)
- [x] 2.4 Implement the final `_normalize_rows` on the base: derive required columns from `set(_column_map.values())`, iterate rows, call `_extract_row`, then `_sort_prices`
- [x] 2.5 Implement `_extract_row` on the base: parse `trade_date`/`open`/`high`/`low`/`close` via the column map, run `_validate_ohlc`, parse `volume` only when `"volume"` in `_column_map` (else `volume=None`), build `DailyPrice(adjusted_close=None)`

## 3. Migrate AkShare provider to subclass

- [x] 3.1 Rewrite `akshare_market_data_provider.py` so `AkShareMarketDataProvider(BaseMarketDataProvider)` provides only: `name="akshare"`, `_source_label="akshare"`, `_column_map` mapping canonical fields to Chinese columns including `volume→成交量`, and `@retry`-decorated `_fetch_rows` calling `self._source.fund_etf_hist_em(symbol=..., period="daily", start_date=..., end_date=..., adjust="")`
- [x] 3.2 Remove the per-provider `_AKSHARE_FETCH_ATTEMPTS` / `_AKSHARE_FETCH_WAIT_SECONDS` duplication by sourcing retry constants from the base (or retain as module constants referenced by the subclass decorator — pick one, keep consistent with Tencent)
- [x] 3.3 Delete the now-redundant module-level parse/validate helpers and the local `MarketDataProviderError` definition from the AkShare module

## 4. Migrate Tencent provider to subclass

- [x] 4.1 Rewrite `tencent_market_data_provider.py` so `TencentMarketDataProvider(BaseMarketDataProvider)` provides only: `name="tencent"`, `_source_label="tencent"`, `_column_map` mapping to English columns with no `volume` key, `_format_request_symbol` applying the `sh`/`sz` prefix (`15*`→`sz`, else `sh`), and `@retry`-decorated `_fetch_rows` calling `self._source.stock_zh_a_hist_tx(symbol=..., start_date=..., end_date=..., adjust="")`
- [x] 4.2 Confirm Tencent inherits the default ascending `_sort_prices` (do not override) — this is the deliberate behavior change captured in the spec delta
- [x] 4.3 Delete the now-redundant module-level parse/validate helpers and the `_to_tx_symbol` free function (folded into `_format_request_symbol`) from the Tencent module

## 5. Update tests

- [x] 5.1 Confirm no AkShare test asserts the `"invalid date"` reason string (grep verified — tests assert source/symbol/date-range/row/column/reason-presence context, not the reason text); the shared `_parse_trade_date` now emits `"invalid trade date"` with no test wording update required
- [x] 5.2 Add a test asserting Tencent returns prices sorted ascending by `trade_date` when the source returns rows in descending/unsorted order (covers the new ordering requirement and the behavior change)
- [x] 5.3 Verify the existing AkShare sorting test still passes (it already asserts ascending order after source returns descending rows)
- [x] 5.4 Optionally extract a shared `test_base_market_data_provider.py` covering the common parsing/validation matrix (missing values, non-numeric, non-positive, inconsistent OHLC, invalid volume) against a fake-subclass harness, to avoid keeping the matrix duplicated across both provider test files
- [x] 5.5 Confirm the retry-sleep monkeypatch fixtures (`AkShareMarketDataProvider._fetch_rows.retry` / `TencentMarketDataProvider._fetch_rows.retry`) still resolve after the base-class move

## 6. Verification

- [x] 6.1 Run `uv run ruff check .` and resolve any new findings
- [x] 6.2 Run `uv run mypy packages/core` and confirm no new type errors
- [x] 6.3 Run `uv run pytest packages/core/tests` and confirm all provider tests pass
- [x] 6.4 Run `uv run pytest tests` for the integration suite
- [x] 6.5 Run `openspec validate deduplicate-market-data-providers --strict` and resolve any reported issues
- [x] 6.6 Grep the codebase for any remaining `akshare_module` keyword or `from vela_core.akshare_market_data_provider import MarketDataProviderError` to confirm full migration

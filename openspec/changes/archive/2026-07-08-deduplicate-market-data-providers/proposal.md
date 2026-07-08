## Why

`AkShareMarketDataProvider` and `TencentMarketDataProvider` share roughly 300 lines of near-verbatim code (`_parse_decimal` / `_parse_price` / `_validate_ohlc` / `_is_missing` / the `get_etf_daily_prices` orchestration / the `_normalize_rows` skeleton), while their genuine differences reduce to a handful of hooks (source call, column names, symbol prefix, volume presence, sort behavior). The duplication was flagged as a high-priority maintainability issue in the 2026-07-08 code quality review ([M1]). Beyond the copy-paste cost, the duplication hides three latent divergences: `MarketDataProviderError` is wrongly owned by the AkShare module and reverse-imported by Tencent; the two providers disagree on result ordering (AkShare sorts ascending, Tencent returns source order); and validation error wording differs (`"invalid date"` vs `"invalid trade date"`). This change extracts a shared base class and closes those gaps.

## What Changes

- Introduce `BaseMarketDataProvider` carrying the shared fetch/normalize orchestration, row parsing (`_parse_decimal` / `_parse_price` / `_parse_volume` / `_parse_trade_date`), validation (`_validate_ohlc` / `_is_missing`), date formatting, and error wrapping. Subclasses override a small hook set: `name`, `_source_label`, `_column_map`, `_fetch_rows`, `_format_request_symbol`, `_sort_prices`.
- `AkShareMarketDataProvider` and `TencentMarketDataProvider` become thin subclasses providing only their hooks (column map, source call, symbol prefix, sort policy, volume column presence).
- Relocate `MarketDataProviderError` from `akshare_market_data_provider.py` into the contract module `market_data_provider.py` (alongside `DailyPrice` and the `MarketDataProvider` Protocol). Update `packages/core/src/vela_core/__init__.py` to re-export it from the new location; the public name `MarketDataProviderError` is unchanged.
- Unify result ordering: both providers return `DailyPrice` sequences sorted ascending by `trade_date`. Tencent's previous reliance on source order is replaced by an explicit ascending sort. Downstream `market_data_fetcher` batch-upserts by primary key, so ordering is not load-bearing for persistence (verified).
- Unify validation error wording to `"invalid trade date"` (consistent with the `_parse_trade_date` helper name). AkShare tests that assert `"invalid date"` are updated.
- Rename the constructor parameter `akshare_module` and attribute `self._akshare` to `source` / `self._source` in both providers. All current call sites (`apps/api`, `apps/cli`) construct with no arguments, so this is a non-breaking signature change in practice.
- Retain all existing per-provider behaviors that genuinely differ: AkShare requires and parses a volume column (`成交量`) and uses Chinese column names; Tencent has no volume column (returns `volume=None`) and drops the `amount` column; Tencent maps bare symbols to `sh`/`sz` prefixes; retry policies stay per-provider (3 attempts / 1s wait) via the `@retry`-decorated `_fetch_rows` hook.

## Capabilities

### New Capabilities

_(none — the base class is an implementation pattern within the existing `market-data-provider` capability, not a new behavioral capability.)_

### Modified Capabilities

- `market-data-provider`: add a daily-price result ordering requirement (ascending by `trade_date`, previously undefined); record that `MarketDataProviderError` is defined at the contract level rather than within a concrete provider implementation. Tencent's observable behavior changes from unspecified order to ascending order.

## Impact

- **Code**: `packages/core/src/vela_core/akshare_market_data_provider.py`, `tencent_market_data_provider.py`, `market_data_provider.py`, `__init__.py`. Net reduction of ~250 lines of duplicated logic.
- **Tests**: `packages/core/tests/test_akshare_market_data_provider.py` and `test_tencent_market_data_provider.py` continue to pass for behavior; AkShare error-wording assertions are updated. A shared base-class test module may be added to cover the common parsing/validation matrix once instead of twice.
- **Public API**: `MarketDataProviderError`, `AkShareMarketDataProvider`, `TencentMarketDataProvider`, `DailyPrice`, `MarketDataProvider` remain exported from `vela_core` with identical names. The constructor keyword `akshare_module` is removed; no internal call site uses it.
- **Spec**: `openspec/specs/market-data-provider/spec.md` gains the ordering requirement and the contract-level error-type note.
- **Risk**: low. All call sites verified; behavior changes are limited to Tencent ordering (safe given PK-based upsert) and a wording string. No persistence, schema, or network-call changes.

## Context

The core package already defines a small market data provider contract: `DailyPrice` for normalized ETF OHLCV rows and `MarketDataProvider` for fetching daily prices by symbol with optional date bounds. Existing market data storage and fetch log models are separate from this provider contract.

AkShare provides ETF historical daily行情 through `fund_etf_hist_em`, returning a pandas DataFrame with Chinese column names such as `日期`, `开盘`, `收盘`, `最高`, `最低`, and `成交量`. Vela needs an adapter that hides this source-specific shape behind the existing internal contract.

## Goals / Non-Goals

**Goals:**

- Provide a concrete AkShare-backed implementation of `MarketDataProvider`.
- Normalize AkShare ETF daily rows into `DailyPrice`.
- Preserve clear error propagation so fetch orchestration can catch failures and record them in `DataFetchLog`.
- Keep the provider independently testable without network access.

**Non-Goals:**

- Do not implement market data ingestion, upsert behavior, scheduling, retry policy, or `DataFetchLog` writes.
- Do not add broker integration, realtime quotes, minute data, LOF, REITs, or ETF metadata symbol mapping.
- Do not make price adjustment configurable in this change.

## Decisions

1. Implement AkShare support as a separate provider module.

   Rationale: `market_data_provider.py` should remain the source-library-independent contract. Keeping AkShare imports in a dedicated module preserves the existing contract independence tests.

   Alternative considered: place the concrete class beside the protocol. This is smaller but mixes the public abstraction with a concrete external dependency.

2. Use AkShare `fund_etf_hist_em` with `period="daily"` and `adjust=""`.

   Rationale: the user confirmed the default should be unadjusted data. Unadjusted OHLC reflects the original market行情 and keeps `adjusted_close=None` semantically honest.

   Alternative considered: default to `qfq` or `hfq`. Those are useful for some strategy calculations, but AkShare adjusts the whole OHLC series rather than returning a separate adjusted close field, which would blur raw price and adjusted price semantics.

3. Convert provider rows into `DailyPrice` using explicit column mapping.

   Rationale: upstream code should not inspect pandas or AkShare-specific column names. Required columns are `日期`, `开盘`, `最高`, `最低`, `收盘`, and `成交量`.

   Alternative considered: pass through the DataFrame for ingestion code to parse. That would violate the existing provider abstraction and duplicate normalization logic in callers.

4. Raise a stable provider exception for source and normalization failures.

   Rationale: upper-layer fetch workflows already have `DataFetchLog.error_message`; they can catch one provider-level exception and record a useful message without knowing AkShare internals.

   Alternative considered: return partial success or error objects from the provider. That would expand the existing `MarketDataProvider` return contract and force all callers and fake providers to handle a new result shape.

5. Add `akshare` as a normal project dependency.

   Rationale: this provider is a production market data source, not only an optional experiment.

   Alternative considered: optional dependency. That keeps installs lighter but makes the default production path fail unless extras are installed.

## Risks / Trade-offs

- AkShare network or upstream schema changes can break fetching -> wrap source and normalization failures in provider errors with symbol and date-range context.
- Empty AkShare results can mean an invalid symbol or no data in range -> return an empty list and let ingestion decide whether that is success, failed, or partial.
- Unadjusted data can distort return calculations around distributions -> leave `adjusted_close=None` so strategy code falls back to raw close explicitly; add adjusted series support later if needed.
- Real AkShare calls are network-dependent -> unit tests use fakes/mocks and avoid live network requirements.

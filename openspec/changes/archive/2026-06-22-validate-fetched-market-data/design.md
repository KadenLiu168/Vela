## Context

Vela already has a source-independent `MarketDataProvider` contract and an AkShare implementation that maps `fund_etf_hist_em` rows into `DailyPrice`. The current provider checks required columns and wraps parsing failures, but it does not explicitly reject row-level nulls, non-positive prices, invalid volume, or inconsistent OHLC relationships.

There is not yet a market data ingestion/upsert service. The safest narrow boundary for this change is therefore the AkShare provider normalization step: invalid fetched data must not become internal `DailyPrice` values.

## Goals / Non-Goals

**Goals:**

- Reject malformed AkShare ETF daily rows before they enter the provider contract.
- Validate required row values, dates, OHLC prices, volume, and basic OHLC consistency.
- Raise actionable `MarketDataProviderError` messages with enough row and source context to diagnose upstream data issues.
- Keep the existing public provider interface unchanged.

**Non-Goals:**

- Do not add a market data ingestion/upsert service.
- Do not write `DataFetchLog` rows in the provider.
- Do not change database schema or ORM constraints.
- Do not add configurable strict/lenient validation modes.
- Do not add adjusted-price support.

## Decisions

1. Validate inside `AkShareMarketDataProvider._normalize_rows`.

   Rationale: this is the first boundary where source-specific rows become internal data. Keeping validation here prevents pandas/AkShare details from leaking into future ingestion code.

   Alternative considered: add validation to `DailyPrice.__post_init__`. That would protect all providers, but it would also make fake provider tests and any future non-AkShare provider inherit AkShare-specific policy decisions before the broader contract is designed.

2. Treat any invalid row as a whole-response failure.

   Rationale: daily price series are time-ordered inputs for signals and backtests. Silently skipping a row can create hidden gaps that look like valid missing market days.

   Alternative considered: skip bad rows and return partial data. That needs explicit partial-ingestion semantics and `DataFetchLog` writes, which are outside the current provider-only scope.

3. Use simple deterministic validation rules.

   Rationale: Phase 1 needs enough protection against source shape and obvious data quality problems without overfitting market microstructure. Required dates and OHLC values must be present, OHLC prices must be positive finite decimals, volume must be a non-negative integer, and high/low must bound open/close.

   Alternative considered: add richer market anomaly checks such as price jump thresholds or trading-calendar validation. Those can produce false positives and need strategy-specific policy.

4. Include source location in provider errors.

   Rationale: users need to diagnose upstream issues quickly. Validation failures should include source, symbol, requested date range, row index, column name, invalid value, and reason where applicable.

   Alternative considered: rely on raw parser exceptions. Those are shorter to implement but often omit the symbol, requested range, and failing source row.

## Risks / Trade-offs

- Strict provider validation can reject rows that AkShare later fixes or represents in an unusual but recoverable way -> keep rules limited to obvious invalid data.
- `NaN` and pandas null handling can be subtle -> test `None`, empty string, and pandas/NumPy null-like values explicitly.
- Whole-response failure blocks otherwise valid rows -> this is intentional until an ingestion layer owns partial writes and fetch log accounting.

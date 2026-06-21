## 1. Contract Tests

- [x] 1.1 Add tests that construct a provider daily price value and verify it exposes symbol, trade date, OHLC, optional adjusted close, and optional volume fields.
- [x] 1.2 Add tests that a fake provider can satisfy `MarketDataProvider` and return deterministic ETF daily prices.
- [x] 1.3 Add tests confirming provider contract usage does not require `MarketPrice`, SQLAlchemy sessions, AkShare, or pandas return shapes.

## 2. Core Implementation

- [x] 2.1 Add a provider-facing module under `vela_core` for market data provider types.
- [x] 2.2 Define the normalized daily price value object with typed fields matching the ETF daily OHLCV contract.
- [x] 2.3 Define the `MarketDataProvider` protocol with a provider name and ETF daily price fetch method accepting a symbol plus optional date bounds.
- [x] 2.4 Export the provider contract from a predictable import path for future ingestion and adapter code.

## 3. Verification

- [x] 3.1 Run the focused provider tests.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run `uv run ruff check .`.

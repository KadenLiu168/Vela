## 1. Tests

- [x] 1.1 Add an AkShare provider test where the source call fails temporarily and succeeds before retries are exhausted.
- [x] 1.2 Add an AkShare provider test where all source-call retry attempts fail and the provider raises `MarketDataProviderError` with source, symbol, and date-range context.
- [x] 1.3 Add an AkShare provider test proving invalid returned rows are not retried.
- [x] 1.4 Add or update fetch workflow coverage proving a provider failure after retry exhaustion is still recorded through existing failed or partial fetch log behavior.

## 2. Dependency

- [x] 2.1 Add `tenacity` to the project runtime dependencies.
- [x] 2.2 Update the lockfile with the resolved `tenacity` dependency.

## 3. Provider Implementation

- [x] 3.1 Define the AkShare retry policy in `akshare_market_data_provider.py` using a finite retry count and simple fixed wait.
- [x] 3.2 Wrap only the `fund_etf_hist_em` source call with the retry policy.
- [x] 3.3 Preserve existing `MarketDataProviderError` wrapping and context after retry exhaustion.
- [x] 3.4 Leave AkShare row normalization and validation outside the retry boundary.

## 4. Verification

- [x] 4.1 Run the AkShare provider test module.
- [x] 4.2 Run market data fetcher and CLI fetch tests to verify logging and command behavior remain unchanged.
- [x] 4.3 Run `openspec status --change "add-market-data-source-retry"` and confirm the change remains apply-ready.

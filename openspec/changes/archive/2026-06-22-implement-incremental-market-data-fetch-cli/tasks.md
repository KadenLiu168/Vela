## 1. Core Workflow

- [x] 1.1 Add tests for inferring incremental fetch start date from the maximum local `MarketPrice.trade_date`.
- [x] 1.2 Add tests for failed incremental fetch behavior when no local market price baseline exists.
- [x] 1.3 Add tests for incremental active ETF filtering, inactive ETF exclusion, provider date bounds, persistence counts, and fetch log fields.
- [x] 1.4 Implement `fetch_incremental_market_prices` in the core market data fetcher using the existing provider, mapping, upsert, and logging boundaries.
- [x] 1.5 Export the incremental fetch workflow from the core package public API.

## 2. CLI Integration

- [x] 2.1 Add CLI tests proving `fetch-market-data --incremental` calls the incremental workflow with the selected database URL.
- [x] 2.2 Add CLI tests proving `fetch-market-data` without `--incremental` still calls the full workflow.
- [x] 2.3 Wire the `--incremental` flag into the existing `fetch-market-data` command while preserving the current summary and exit-code behavior.
- [x] 2.4 Update CLI documentation with the incremental command example and baseline behavior.

## 3. Validation

- [x] 3.1 Run the targeted CLI and core market data tests.
- [x] 3.2 Run the full test suite with `uv run pytest`.
- [x] 3.3 Run `uv run ruff check .` and fix issues introduced by this change.
- [x] 3.4 Verify `openspec status --change "implement-incremental-market-data-fetch-cli"` reports the change as ready for implementation.

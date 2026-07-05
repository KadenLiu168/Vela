## ADDED Requirements

### Requirement: Full market price fetch succeeds for the configured pool
The system SHALL successfully persist daily market prices for every active ETF in the configured pool when `vela fetch-market-data` (full mode) runs against a local SQLite database whose `SQLITE_MAX_VARIABLE_NUMBER` uses the SQLite default (32766).

#### Scenario: Full fetch for the Phase 1 ETF pool completes
- **WHEN** a developer runs `uv run vela fetch-market-data` against an empty local `vela.db` and the configured `phase1_core` pool contains 6 active ETFs with full daily history
- **THEN** the command completes without raising a database parameter-limit error
- **AND** every fetched `(etf_id, trade_date)` row exists in the `market_price` table

#### Scenario: Large upsert stays under the SQLite parameter limit
- **WHEN** backend code calls `upsert_market_prices` with more than 18,000 `MarketPrice` rows in a single invocation
- **THEN** the call does not raise `sqlite3.OperationalError: too many SQL variables` from either the existing-key detection SELECT or the INSERT itself
- **AND** the returned `MarketPriceUpsertResult` reports the same total `rows_inserted` and `rows_updated` counts as a single-statement execution would

#### Scenario: Existing-key detection is preserved across SELECT batches
- **WHEN** backend code calls `upsert_market_prices` with a number of keys that require multiple SELECT batches
- **THEN** the union of the per-batch existing-key results equals the set of keys that would be returned by a single unchunked `IN` query
- **AND** rows whose `(etf_id, trade_date)` exists in the database are reported as `rows_updated`, not `rows_inserted`

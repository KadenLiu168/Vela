## 1. Tests

- [x] 1.1 Add a unit test that calls `upsert_market_prices` with >18,000 `MarketPrice` rows in a single invocation against a temporary SQLite database; assert the call succeeds, the row count matches the input, and no `sqlite3.OperationalError` is raised.
- [x] 1.2 Add a unit test that pre-inserts 50 rows, then calls `upsert_market_prices` with >18,000 rows where those 50 are duplicated with different values; assert the returned `rows_inserted` and `rows_updated` equal the expected split and the database rows reflect the new values for the overlapping keys.
- [x] 1.3 Run the new tests first against the current implementation and confirm they reproduce the original `sqlite3.OperationalError: too many SQL variables` failure (on both the SELECT IN and the INSERT paths) before the implementation change.

## 2. Implementation

- [x] 2.1 In `packages/core/src/vela_core/market_price_upsert.py`, add a module-level constant `BATCH_SIZE: int = 16_000` with a comment noting it is sized for the current 2-column `(etf_id, trade_date)` key (`16_000 × 2 = 32_000` < SQLite's default `SQLITE_MAX_VARIABLE_NUMBER = 32_766`).
- [x] 2.2 Refactor `_existing_market_price_keys` to slice `keys` into batches of `BATCH_SIZE` and call `session.execute(...)` once per batch, taking the union of the per-batch results into the returned `set`.
- [x] 2.3 Change `upsert_market_prices`' INSERT call from `insert(MarketPrice).values(rows)` + `session.execute(statement)` to `insert(MarketPrice).on_conflict_do_update(...)` + `session.execute(statement, rows)` so SQLAlchemy 2.0 routes the INSERT through SQLite's `insertmanyvalues` optimization and auto-chunks the bind parameters.
- [x] 2.4 Re-run the unit tests from section 1 and confirm they pass.

## 3. Verification

- [x] 3.1 Run `uv run ruff check .` and resolve any new lint findings introduced by the change.
- [x] 3.2 Run `uv run ruff format --check .` and confirm the touched files are formatted.
- [x] 3.3 Run the focused test file (`uv run pytest packages/core/tests/test_market_price_upsert.py`) and then the full `uv run pytest` to confirm no regressions.
- [x] 3.4 Reset the local database (`rm -f vela.db`) and run `uv run vela init-db && uv run vela sync-etf-pool && uv run vela fetch-market-data` end-to-end; confirm the fetch completes without `too many SQL variables` and reports expected `rows_inserted` / `rows_updated` counts.
- [x] 3.5 Run `openspec validate fix-market-price-upsert-chunking` and confirm the change is apply-ready.

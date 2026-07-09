## 1. Model & migration

- [x] 1.1 Add `quality_warnings: Mapped[str | None] = mapped_column(Text)` to `DataFetchLog` in `packages/core/src/vela_core/models/data_fetch_log.py` (import `Text` if missing)
- [x] 1.2 Create `alembic/versions/20260709_0008_add_data_fetch_log_quality_warnings.py` migration that adds nullable `quality_warnings` column to `data_fetch_log` (down_revision = `20260708_0007_...`)
- [x] 1.3 Verify the new column appears via both DB init paths: fresh `initialize_database` (create-all) and `alembic upgrade head` on an existing DB

## 2. Duplicate detection pure function

- [x] 2.1 Create `packages/core/src/vela_core/data_quality.py`
- [x] 2.2 Define `DuplicateTradeDateWarning` frozen dataclass with `etf_id: int`, `trade_date: date`, `count: int`
- [x] 2.3 Implement `detect_duplicate_trade_dates(prices: Sequence[MarketPrice]) -> list[DuplicateTradeDateWarning]` as a pure function: count `(etf_id, trade_date)` occurrences, return keys with count > 1; must not mutate input, must not hold a session
- [x] 2.4 Implement `build_quality_warnings_json(warnings: Sequence[DuplicateTradeDateWarning]) -> str | None` envelope builder producing `{"duplicate_trade_dates": [{"etf_id":..,"trade_date":"<ISO>","count":..}, ...]}`; return `None` when empty

## 3. Fetcher wiring

- [x] 3.1 Add `quality_warnings: str | None = None` field to `MarketDataFetchResult` in `market_data_fetcher.py`
- [x] 3.2 Add `quality_warnings: str | None` parameter to `_finish_log` and assign to `fetch_log.quality_warnings`
- [x] 3.3 In `_fetch_market_prices`, run `detect_duplicate_trade_dates(market_prices)` before `upsert_market_prices`, build the JSON envelope, and pass it to `_finish_log` and the returned `MarketDataFetchResult` (apply to both the success path and the early-return failure paths where no batch exists → `None`)

## 4. Unit tests for detection

- [x] 4.1 Create `packages/core/tests/test_data_quality.py`
- [x] 4.2 `detect_duplicate_trade_dates` returns empty list when no duplicates
- [x] 4.3 `detect_duplicate_trade_dates` returns warnings with correct `count` for duplicate `(etf_id, trade_date)` keys
- [x] 4.4 `detect_duplicate_trade_dates` does not mutate its input and holds no session
- [x] 4.5 `build_quality_warnings_json` returns `None` for empty input and the expected JSON shape for non-empty input

## 5. Fetcher integration tests

- [x] 5.1 Extend `packages/core/tests/test_market_data_fetcher.py`: a fetch batch with duplicate `(etf_id, trade_date)` persists `quality_warnings` JSON on the `DataFetchLog` row
- [x] 5.2 A fetch batch with no duplicates leaves `DataFetchLog.quality_warnings` null
- [x] 5.3 The returned `MarketDataFetchResult.quality_warnings` matches the persisted log value
- [x] 5.4 Dedup semantics are unchanged: last-write-wins still applies and the upsert is not blocked by warnings

## 6. Validation

- [x] 6.1 `ruff format` + `ruff check` pass
- [x] 6.2 `mypy` passes
- [x] 6.3 `pytest packages/core/tests` green
- [x] 6.4 `openspec validate --all` green

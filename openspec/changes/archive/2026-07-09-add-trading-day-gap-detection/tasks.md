## 1. Detectors and envelope builder

- [x] 1.1 Add `SystematicTradingDayGap` frozen dataclass (`trade_date: date`) to `data_quality.py`
- [x] 1.2 Add `EtfTradingDayGap` frozen dataclass (`etf_id: int`, `trade_date: date`) to `data_quality.py`
- [x] 1.3 Implement `detect_systematic_trading_day_gaps(actual_dates, expected_dates) -> list[SystematicTradingDayGap]` (set difference, sorted ascending, pure)
- [x] 1.4 Implement `detect_etf_trading_day_gaps(etf_actual_dates, expected_dates, inception_boundaries) -> list[EtfTradingDayGap]` (per-ETF set difference with inception-boundary suppression, sorted by `(etf_id, trade_date)`, pure)
- [x] 1.5 Implement `build_quality_warnings_json_from_sections(duplicates, systematic_gaps, etf_gaps) -> str | None` (multi-section JSON envelope, omit empty sections, return `None` when all empty, `duplicate_trade_dates` serialization identical to Phase 1)
- [x] 1.6 Keep the Phase 1 `build_quality_warnings_json` unchanged

## 2. Fetch hook wiring

- [x] 2.1 In `market_data_fetcher._fetch_market_prices`, after the upsert, query `trading_calendar` for `[range_start, range_end]`
- [x] 2.2 When the calendar has covering rows, query the stored trade-date union and per-ETF stored dates for the same range
- [x] 2.3 Compute per-ETF inception boundaries as `max(inception_date, first_stored_date)` (skip ETFs with no stored rows)
- [x] 2.4 Run `detect_systematic_trading_day_gaps` and `detect_etf_trading_day_gaps`, then merge with duplicate warnings via `build_quality_warnings_json_from_sections`
- [x] 2.5 When the calendar has no covering rows, skip gap detection and write only duplicate warnings (Phase 1 behavior)
- [x] 2.6 Ensure gap detection never changes `status` or `error_message` (warn-only)

## 3. Backtest hook and strict config

- [x] 3.1 Add `BacktestGapDetectionConfig` frozen dataclass (`strict: bool`, `max_systematic_gaps: int`) to `backtest_runner.py`
- [x] 3.2 Add optional `gap_detection: BacktestGapDetectionConfig | None = None` parameter to `run_backtest`
- [x] 3.3 In `run_backtest`, after `_load_trading_dates`, query `trading_calendar` for `[start_date, end_date]`
- [x] 3.4 When the calendar has covering rows, resolve the union (already `trading_dates`), query per-ETF stored dates, compute inception boundaries, and run both detectors
- [x] 3.5 Default mode (`gap_detection is None` or `strict=False`): print detected gaps (or a "calendar not synced" warning when empty) and continue
- [x] 3.6 Strict mode (`strict=True`): raise without persisting when systematic gap count exceeds `max_systematic_gaps`; raise when the calendar is empty (cannot strict-check without a reference); never raise on per-ETF-only gaps (warn instead)

## 4. CLI flags

- [x] 4.1 Add `--strict-data-quality` (store_true) argument to the `run-backtest` subparser
- [x] 4.2 Add `--max-gap-days` argument (type int, default `5`) to the `run-backtest` subparser
- [x] 4.3 In the `run-backtest` dispatch, construct `BacktestGapDetectionConfig` from the flags and pass it as `gap_detection` to the CLI `run_backtest` wrapper
- [x] 4.4 Update the CLI `run_backtest` wrapper signature to accept and forward `gap_detection`

## 5. Exports

- [x] 5.1 Export `SystematicTradingDayGap`, `EtfTradingDayGap`, `detect_systematic_trading_day_gaps`, `detect_etf_trading_day_gaps`, `build_quality_warnings_json_from_sections`, `BacktestGapDetectionConfig` from `vela_core/__init__.py` (imports + `__all__`)

## 6. Unit tests

- [x] 6.1 `test_data_quality.py`: `detect_systematic_trading_day_gaps` — gap detected, no gaps when matching, extra stored dates ignored, deterministic ordering
- [x] 6.2 `test_data_quality.py`: `detect_etf_trading_day_gaps` — gap after inception, suppressed before inception boundary, no gaps when covered, ordering across ETFs, ETF with no stored rows is skipped
- [x] 6.3 `test_data_quality.py`: `build_quality_warnings_json_from_sections` — merge all three sections, empty returns `None`, duplicate-only matches Phase 1 serialization, gap-only omits empty duplicate section

## 7. Integration tests

- [x] 7.1 `test_market_data_fetcher.py`: fetch with a gap in stored data and a covering calendar records `trading_day_gaps` in `quality_warnings`
- [x] 7.2 `test_market_data_fetcher.py`: fetch with an empty `trading_calendar` skips gap detection and writes only duplicate warnings (or `None`)
- [x] 7.3 `test_market_data_fetcher.py`: fetch with gaps and duplicates in the same batch records both sections
- [x] 7.4 `test_backtest_runner.py`: default mode warns and proceeds when systematic gaps exist
- [x] 7.5 `test_backtest_runner.py`: strict mode raises when systematic gaps exceed the threshold
- [x] 7.6 `test_backtest_runner.py`: strict mode tolerates gaps within the threshold and proceeds
- [x] 7.7 `test_backtest_runner.py`: per-ETF-only gaps never trigger strict failure
- [x] 7.8 `test_backtest_runner.py`: empty calendar in default mode warns and proceeds; empty calendar in strict mode raises

## 8. Validation

- [x] 8.1 Run `uv run ruff format` and `uv run ruff check` on changed files
- [x] 8.2 Run `uv run mypy packages/core/src/vela_core`
- [x] 8.3 Run `uv run pytest packages/core/tests apps/api/tests apps/cli/tests`
- [x] 8.4 Run `openspec validate --all`

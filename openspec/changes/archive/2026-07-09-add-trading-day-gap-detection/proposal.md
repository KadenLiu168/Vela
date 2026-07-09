## Why

Phase 1 (`add-market-data-quality-warnings`) added a `quality_warnings` soft-signal
channel and the first detector — duplicate trade dates — but the second, more
dangerous data-quality hole is still open: **trading-day gaps**.

`backtest_runner._load_trading_dates` builds the backtest trading-day sequence
with `SELECT DISTINCT trade_date FROM market_price` — i.e. the union of whatever
rows happen to be stored. When the source is missing a trading day (provider
outage, sync skipped, partial fetch), that day simply is not in the union and the
sequence silently continues. Because `momentum_scoring._calculate_window_return`
indexes by **stored-row position** (`prices[-1 - window]`), a missing day shifts
position N to an earlier calendar day than intended, so an "N trading-day" window
silently spans the wrong time range. The spec defines windows as "N rows back",
which is only equivalent to "N trading days back" when the data is complete.

The result is the failure mode that motivated this whole effort: the backtest
finishes without error, the curve looks plausible, but the numbers are computed
against a shifted time range, and there is no record that the data was ever
incomplete. "Does not crash, only silently wrong, and untraceable afterwards."

`add-trading-calendar` (change 1) just landed the reference source — the
`trading_calendar` table populated from akshare's `tool_trade_date_hist_sina`.
This change consumes it: compare "trading days that should exist" against "trading
days actually stored" and surface the gaps before they corrupt a backtest.

## What Changes

**New detector functions (pure, session-free)** in `data_quality.py`:

- `detect_systematic_trading_day_gaps(actual_dates, expected_dates)` — finds
  trading days present in the calendar but absent from the **union** of all ETFs'
  stored dates. These are the gaps that shift `_load_trading_dates` and corrupt
  position-indexed windows; they are the strict-mode candidates.
- `detect_etf_trading_day_gaps(etf_actual_dates, expected_dates, inception_dates)`
  — per-ETF gaps, suppressed before each ETF's `inception_date` (and before its
  first stored row) to avoid flagging pre-listing or suspended periods as gaps.

**Envelope extension.** `quality_warnings` JSON gains a sibling
`trading_day_gaps` key alongside the existing `duplicate_trade_dates`, so the
two detectors coexist without breaking existing consumers. A new multi-section
builder merges them; the Phase 1 single-section builder is kept for backward
compatibility.

**Fetch hook (warn-only).** `market_data_fetcher` runs gap detection after
upsert (so it inspects the post-write DB state) and records the result in
`DataFetchLog.quality_warnings`. Fetch is warn-only — incremental ranges are
short and routinely contain holidays, so strict here would be noisy.

**Backtest hook (warn default, strict opt-in).** `backtest_runner` runs gap
detection right after `_load_trading_dates`. By default it warns (prints the
gaps). An opt-in strict mode, enabled via a `--strict-data-quality` CLI flag with
a configurable `--max-gap-days` threshold, raises when systematic gaps exceed
the threshold — blocking the run before it produces misleading numbers.
Per-ETF gaps are always warn-only (they are usually suspensions, not corruption).

**No-calendar graceful degrade.** When `trading_calendar` is empty (user has not
run `vela sync-trading-calendar` yet), gap detection is skipped with a clear
warning rather than failing. Strict mode refuses to run without a calendar (a
strict check has no reference to check against), so it raises in that case.

**No spec-mandated behavior changes.** Deduplication stays last-write-wins
(`market-data` spec requirement, unchanged). Window calculation stays "N rows
back" (`market-data` spec requirement, unchanged). This change only **adds
detection and surfacing**; the underlying computation semantics are untouched.
The root-cause fix (re-anchoring windows to real trading-day offsets) is a
separate, larger follow-up and explicitly out of scope.

## Capabilities

### New Capabilities
- `trading-day-gap-detection`: Pure detector functions that compare stored
  market-price trade dates against the trading calendar to find missing trading
  days, split into systematic (union-level) and per-ETF gaps, plus the
  multi-section `quality_warnings` envelope builder that combines them with
  duplicate-date warnings.

### Modified Capabilities
- `market-data`: Adds a requirement that the fetch workflow records trading-day
  gap warnings in `DataFetchLog.quality_warnings` after upsert (warn-only).
- `backtest-execution`: Adds a requirement that the backtest workflow runs gap
  detection after loading trading dates, warns by default, and optionally fails
  fast (strict, opt-in) when systematic gaps exceed a threshold.

## Impact

- **Code**:
  - `packages/core/src/vela_core/data_quality.py` — new gap detectors + multi-section envelope builder
  - `packages/core/src/vela_core/market_data_fetcher.py` — fetch hook (post-upsert gap detection)
  - `packages/core/src/vela_core/backtest_runner.py` — backtest hook (warn default / strict opt-in)
  - `apps/cli/src/vela_cli/main.py` — `--strict-data-quality` / `--max-gap-days` flags on `run-backtest`
  - `packages/core/src/vela_core/__init__.py` — exports
- **Tests**:
  - `packages/core/tests/test_data_quality.py` — gap detector unit tests
  - `packages/core/tests/test_market_data_fetcher.py` — fetch hook integration
  - `packages/core/tests/test_backtest_runner.py` — backtest warn + strict integration
  - `apps/cli/tests/` — CLI flag tests
- **Specs**: new `trading-day-gap-detection` capability; modified `market-data` and `backtest-execution`
- **Dependencies**: depends on `trading-calendar` capability (landed). No new third-party deps.
- **No migrations**: reuses the Phase 1 `quality_warnings` column; no schema change.
- **No breaking changes**: all new behavior is additive; existing backtests keep running (warn-only by default).

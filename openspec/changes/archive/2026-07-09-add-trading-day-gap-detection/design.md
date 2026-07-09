# Design: Trading Day Gap Detection

## Context

Phase 1 (`add-market-data-quality-warnings`) introduced the
`DataFetchLog.quality_warnings` nullable JSON column and a single detector —
duplicate trade dates — wired into the fetch pipeline. Change 1
(`add-trading-calendar`) landed the `trading_calendar` table populated from
akshare's `tool_trade_date_hist_sina`, giving us an authoritative "which days
are trading days" reference for A-shares.

This change closes the second half of the data-quality story: detecting
**trading-day gaps** — calendar trading days that should have a stored
`MarketPrice` row but do not. The dangerous one is the **systematic** gap, where
*no* ETF has data for a calendar trading day, because
`backtest_runner._load_trading_dates` builds the backtest sequence from
`SELECT DISTINCT trade_date` (the union). A systematic gap silently drops out of
the union, and because `momentum_scoring._calculate_window_return` indexes by
stored-row position (`prices[-1 - window]`), the window shifts to an earlier
calendar range than intended. The backtest finishes, the curve looks plausible,
and nothing records that the data was incomplete.

Constraints inherited from the codebase:
- Detectors are **pure, session-free functions** (Phase 1 pattern) so they unit-test without a DB.
- Deduplication stays **last-write-wins** (`market-data` spec requirement) — detection only, never change upsert semantics.
- Window calculation stays **"N rows back"** (`market-data` spec requirement) — the root-cause fix (re-anchoring to trading-day offsets) is a separate, larger follow-up and out of scope here.
- `BacktestRun` has no `quality_warnings` column and this change adds **no migration** — backtest gaps are surfaced via print (warn) or raise (strict).

## Goals / Non-Goals

**Goals**
- Detect systematic gaps (calendar vs union) and per-ETF gaps (calendar vs per-ETF, inception-suppressed).
- Wire detection into both the fetch pipeline (warn, into `quality_warnings`) and the backtest pipeline (warn default, strict opt-in).
- Gracefully degrade when the calendar is empty.
- Keep the Phase 1 duplicate detector and envelope backward-compatible.

**Non-Goals**
- Re-anchoring momentum/MA windows to real trading-day offsets (root-cause fix; separate follow-up).
- Detecting suspensions as a distinct class (no suspension calendar exists; per-ETF gaps are treated as warn-only noise).
- A `quality_warnings` column on `BacktestRun` (out of scope; backtest surfaces gaps via print/raise).
- Joinquant calendar support (akshare single-source for now, matching change 1).

## Decisions

### D1: Split gaps into two classes — systematic vs per-ETF
**Decision.** Two detectors: `detect_systematic_trading_day_gaps` (calendar vs
union) and `detect_etf_trading_day_gaps` (calendar vs per-ETF, inception-suppressed).

**Why.** The two classes have different causes and must be handled differently.
A systematic gap (every ETF missing the same calendar day) is almost always
corruption — a source outage or skipped sync — and is exactly what shifts the
union sequence, so it is the strict-mode candidate. A per-ETF gap (one ETF
missing a day others have) is frequently a legitimate suspension, so it must
never trigger strict failure. Collapsing them into one detector would force
callers to re-derive the distinction, duplicating logic and risking a suspension
being treated as corruption.

**Alternative.** A single `detect_trading_day_gaps` returning all gaps with a
`kind` field. Rejected: the detection inputs differ (union vs per-ETF map), and
strict-vs-warn handling is cleaner when the type itself carries the class.

### D2: Pure function signatures
**Decision.**
```
detect_systematic_trading_day_gaps(
    actual_dates: Sequence[date],
    expected_dates: Sequence[date],
) -> list[SystematicTradingDayGap]

detect_etf_trading_day_gaps(
    etf_actual_dates: Mapping[int, Sequence[date]],
    expected_dates: Sequence[date],
    inception_boundaries: Mapping[int, date],
) -> list[EtfTradingDayGap]
```
`SystematicTradingDayGap` and `EtfTradingDayGap` are frozen dataclasses carrying
the missing `trade_date` (and `etf_id` for the per-ETF case). Both functions
return sorted output for determinism and do not mutate inputs.

**Why.** Callers (fetcher, backtest) already have or can cheaply query the
actual dates and the calendar; passing them in keeps the detector testable
without a session and lets the same function serve both call sites. The
`inception_boundaries` map (not raw `inception_date`) lets the caller compute
`max(inception_date, first_stored_date)` once, so the detector stays a pure
function of its arguments.

**Alternative.** Have the detectors query the DB themselves. Rejected: breaks
the pure-function pattern established in Phase 1 and couples detection to the
session, making unit tests heavier.

### D3: Multi-section envelope builder, keep Phase 1 builder
**Decision.** Add `build_quality_warnings_json_from_sections(...)` that accepts
duplicate warnings, systematic gaps, and per-ETF gaps, and emits a JSON envelope
with top-level keys `duplicate_trade_dates`, `systematic_trading_day_gaps`,
`etf_trading_day_gaps` — omitting empty sections. Keep the Phase 1
`build_quality_warnings_json` unchanged for backward compatibility.

**Why.** Phase 1's builder has a fixed signature (duplicates only) and is
already wired into the fetcher. Changing its signature would be a breaking edit
to working code for no benefit. A new multi-section builder lets the fetcher
merge both detectors' output into one envelope while the Phase 1 builder remains
valid for any caller that only cares about duplicates. The
`duplicate_trade_dates` section serializes identically in both, so existing
consumers see no change.

**Alternative.** Mutate `build_quality_warnings_json` to accept optional gap
args. Rejected: widens a working function's surface and risks the Phase 1
duplicate-only behavior drifting.

### D4: Fetch hook runs after upsert, warn-only
**Decision.** In `market_data_fetcher._fetch_market_prices`, after the upsert,
query the trading calendar for `[range_start, range_end]`; if it has rows,
query the stored union and per-ETF dates for the same range, run both
detectors, and merge the result with the duplicate warnings via the multi-section
builder into `quality_warnings`. If the calendar has no covering rows, skip gap
detection (write only duplicate warnings, as today). Fetch gap detection is
always warn-only — it never changes status or `error_message`.

**Why.** Inspecting the post-upsert DB state means the gap check reflects what
was actually persisted, not just what the provider returned. Warn-only keeps
fetch non-blocking: incremental ranges are short and routinely contain holidays,
so strict here would be noisy and would block ingestion on a data-quality
signal — the wrong layer for a hard gate.

**Alternative.** Detect gaps on the in-memory `market_prices` batch before
upsert. Rejected: that only sees the freshly fetched rows, not the union, so it
cannot find systematic gaps that span prior syncs.

### D5: Backtest hook runs after `_load_trading_dates`, default warn / strict opt-in
**Decision.** In `backtest_runner.run_backtest`, immediately after
`_load_trading_dates` resolves `trading_dates`, run gap detection against the
calendar. Default mode prints the gaps and continues. Strict mode raises without
persisting a run when systematic gaps exceed a threshold; per-ETF gaps are
always warn-only.

**Why.** This is the value point: it is the last chance to stop a backtest from
computing metrics against a shifted time range. Placing it right after
`_load_trading_dates` means the check runs before `generate_rebalance_dates`,
`load_price_panel`, and signal generation — so a strict failure wastes no
computation. Warn-by-default preserves existing runs (same rationale as Phase 1:
default strict would break historical runs that already have gaps).

**Alternative.** Gate at the fetch layer only. Rejected: fetch can't protect a
backtest that runs against stale data fetched before the calendar was synced, and
fetch is warn-only by design.

### D6: Strict config via CLI flag + core optional param, no AppConfig change
**Decision.** Add `--strict-data-quality` (bool flag) and `--max-gap-days`
(default `5`) to the `run-backtest` CLI subcommand. The CLI wrapper constructs a
`BacktestGapDetectionConfig` dataclass (`strict: bool`, `max_systematic_gaps:
int`) and passes it as an optional `gap_detection` argument to
`backtest_runner.run_backtest`. `run_backtest` defaults `gap_detection=None`,
meaning warn-only. Do **not** add anything to `AppConfig` or `StrategyConfig`.

**Why.** Data-quality strictness is an execution-time decision, not a strategy
or application property — it does not belong in the strategy YAML or app config.
A CLI flag makes the opt-in explicit per run and keeps the config surface
unchanged. Defaulting the core function to `None` (warn) means programmatic
callers (API, tests) keep working without changes.

**Alternatives.**
- Add a `data_quality` section to `AppConfig`. Rejected: would require YAML
  schema changes and a config reload to toggle, and conflates execution
  strictness with app configuration.
- Add to `StrategyConfig`. Rejected (decided in explore): this is data quality,
  not a strategy parameter; mixing them muddies the strategy contract.

### D7: No-calendar graceful degrade
**Decision.** When the `trading_calendar` table has no rows covering the
requested range:
- **Fetch**: skip gap detection, write only duplicate warnings (behavior
  identical to Phase 1 for that log row).
- **Backtest default**: print a warning that the calendar is not synced and
  proceed without gap detection.
- **Backtest strict**: raise, explaining that strict mode requires a synced
  calendar (a strict check has no reference to check against).

**Why.** Change 1 landed the table but the user may not have run
`vela sync-trading-calendar` yet, or may have synced a range that does not cover
this run. Failing hard on an empty calendar would make this change a regression
for anyone who hasn't synced. Strict mode is the one exception: a strict
guarantee that means nothing without a reference is worse than a clear refusal.

### D8: Per-ETF inception boundary = max(inception_date, first_stored_date)
**Decision.** The caller computes `inception_boundary = max(inception_date,
first_stored_date)` per ETF and passes it to `detect_etf_trading_day_gaps`. The
detector suppresses any gap before that boundary.

**Why.** `inception_date` alone is not enough: an ETF may have been listed years
ago but only fetched starting last month. Flagging every calendar day between
`inception_date` and the first stored row would drown the user in false
positives. Using `max(inception_date, first_stored_date)` means we only check
the range where the ETF demonstrably has history, so a gap there is meaningful
(suspension or source drop). The caller owns this computation so the detector
stays pure.

## Risks / Trade-offs

- **[Per-ETF false positives from suspensions]** → Mitigation: per-ETF gaps are
  warn-only in both fetch and backtest, and the inception boundary suppresses
  the pre-history range. Strict mode never triggers on per-ETF gaps.
- **[Strict mode breaks existing runs if defaulted on]** → Mitigation: strict is
  opt-in via CLI flag; the core function defaults to warn-only.
- **[Calendar not synced → silent skip hides gaps]** → Mitigation: both fetch
  and backtest print a clear warning when the calendar is empty; strict mode
  refuses to run. The skip is loud, not silent.
- **[Fetch gap detection adds two queries per fetch]** → Mitigation: the
  calendar query and the union/per-ETF query are bounded by the requested range
  and are cheap relative to the network upsert that just ran. Acceptable.
- **[Threshold default is a guess]** → Mitigation: `--max-gap-days` is
  configurable; default `5` tolerates a handful of suspensions/outages while
  catching a multi-day source outage.
- **[Does not fix the root cause]** → Trade-off: this change detects and
  surfaces; the position-indexed window semantics remain. Accepted — the
  root-cause fix (re-anchoring to trading-day offsets) touches every pure
  function and the spec's window definition, and is tracked as a separate
  follow-up.

## Migration Plan

No schema migration (reuses Phase 1 `quality_warnings` column). Deploy is purely
additive code. Rollback is code removal — `quality_warnings` reverts to
duplicate-only behavior, and `run_backtest` reverts to no gap check. No data
conversion is needed because gap warnings are transient (per-fetch / per-run),
not referenced by other tables.

## Open Questions

- **Threshold default.** `--max-gap-days` defaults to `5`. This is a judgment
  call; if real-world backtests routinely have a handful of benign per-ETF gaps
  it should be raised, but since strict only counts *systematic* gaps, `5` is
  conservative (5 systematic gaps means the source was down for a week).

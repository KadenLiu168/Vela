## Context

`run_backtest` currently resolves `trading_dates` from the distinct union of `MarketPrice.trade_date`, then compares that union with `TradingCalendar`. Default gap handling warns and continues; opt-in strict mode only blocks systematic gaps above a configurable threshold and never blocks per-ETF gaps. The loaded price panel starts from an approximate calendar buffer (`max_window * 2 + 10`), and historical signal generation may persist partial/failed signals from incomplete inputs.

The equity curve independently treats a missing previous or current price for a held ETF as zero interval return by leaving its market value unchanged. If the next interval also lacks one endpoint, the eventual price move can be omitted rather than caught up. Volatility and Sharpe still count each produced point as one daily observation.

The accepted policy is correctness-first: an official trading day whose missing price can affect strategy calculation or current-holding valuation is invalid input. Vela will not infer suspension, forward-fill, synthesize a price, or allow a warning/threshold to weaken this rule.

## Goals / Non-Goals

**Goals:**

- Use `TradingCalendar` as the authoritative requested-date and lookback-session axis.
- Validate the exact price inputs required by the configured active ETF universe before generating or persisting signals.
- Fail equity calculation if a held-position interval lacks either endpoint price.
- Make failures deterministic, actionable, and atomic with respect to caller-managed transactions.
- Preserve results for complete datasets.

**Non-Goals:**

- Model suspension status or suspension-period valuation.
- Repair, fetch, or forward-fill missing market data during a backtest.
- Change fetch-time warn-only quality logging.
- Change strategy formulas, portfolio drift, T+1 timing, transaction costs, or metric annualization.
- Backfill, delete, relabel, or regenerate historical runs.

## Decisions

### 1. Resolve requested and lookback sessions from `TradingCalendar`

The requested equity-curve dates are the ordered official calendar rows within the inclusive backtest range. A range with no official sessions or insufficient preceding rows for the exact lookback count is a hard error. `TradingCalendar` is the local authority; validating whether its upstream source itself omitted an official session requires separate calendar-provenance metadata and is outside this Change.

The runner will derive the strategy history requirement from `resolve_strategy(config).lookback_days()` and select the exact preceding official sessions needed before the first rebalance date. It will not retain the approximate `max_window * 2 + 10` buffer as the definition of required completeness. The price panel may load a containing date range for query efficiency and for the existing data snapshot, but validation is against the exact required calendar-date set; dates in a loaded superset do not expand that set.

Using the stored-price union was rejected because a date missing from every ETF disappears from both the curve and its observation count. Keeping the calendar optional was rejected because fail-fast completeness has no authoritative reference without it.

### 2. Validate the configured active universe before any backtest write

For this runner, the configured active universe is the `active_etfs` collection passed to the resolved strategy. Every such ETF can affect ranking, defensive selection, equal-weight allocation, or later holdings, so its required price history is validated before `generate_historical_strategy_signals`.

For each active ETF:

- required dates start at the later of the exact lookback start and its declared `inception_date`;
- when `inception_date` is absent, the exact lookback start applies;
- every official required date through the backtest end must have one stored price row;
- an ETF with no required rows is valid only when its declared inception is after the calculation range.

Historical signal generation will pass only ETFs whose declared inception is on or before that signal date to the resolved strategy. For every dated invocation it will also exclude that ETF's stored rows before its declared inception from the strategy-visible price panel. This prevents `equal_weight` or another price-independent strategy from allocating a not-yet-listed ETF and prevents stray pre-inception rows from satisfying or influencing a lookback calculation. The ETF joins the candidate universe on the first signal date on or after inception and is then subject to the same mandatory price validation.

The validator reports deterministic sorted `(etf_id, trade_date)` gaps and raises before the persistence callback can create a signal. Using `first_stored_date` as an eligibility boundary was rejected because it can disguise a truncated or corrupt history as pre-inception time.

### 3. Remove configurable tolerance from backtest execution

`BacktestGapDetectionConfig`, the `gap_detection` parameter, its public export, and the CLI strictness/threshold flags are removed. Once a gap is known to affect required strategy or valuation input, neither a threshold nor non-strict mode is semantically valid.

Keeping the objects as ignored compatibility shims was rejected because their names would promise a relaxation the system no longer honors. Fetch-time gap warnings remain unchanged because ingestion observability and backtest admissibility are separate contracts.

### 4. Keep a defensive held-price guard inside equity calculation

Even after runner preflight, `calculate_strategy_equity_curve` remains a public package API and can be called directly. `_mark_to_market` therefore raises when a currently held ETF lacks either interval endpoint row. The error identifies the ETF and missing date(s).

This guard checks only ETFs economically held at the interval start. A new target first effective at the interval end does not receive the preceding interval return; runner preflight has already established its required price coverage for subsequent valuation. Existing T+1 and rebalance attribution remain unchanged.

Silent value carry, zero contribution, forward fill, and catch-up-on-reopen were rejected because Vela lacks authoritative suspension state and cannot distinguish suspension from corrupted data.

### 5. Preserve caller-owned atomicity

All calendar and strategy-universe completeness checks run before historical signal generation. A preflight failure therefore creates no signals, backtest run, equity rows, or signal links. The direct equity guard performs no persistence itself; if reached through `run_backtest` because of an unexpected inconsistency, the exception propagates through the caller-managed session so the caller can roll back the whole unit of work.

No internal `commit()` or persistent repair is introduced.

### 6. Verify the semantic boundary, not only the exception

Tests will cover:

- a systematic official-day gap;
- a single active-universe ETF/date gap used by strategy calculation;
- missing calendar coverage;
- pre-inception dates excluded and post-inception dates required;
- a not-yet-incepted ETF excluded from each dated strategy candidate universe and included on the first signal date on or after inception;
- stored pre-inception rows excluded from the strategy-visible history;
- missing previous and current held-price endpoints through the direct equity API;
- no writes after runner preflight failure;
- unchanged exact signals, curve, and metrics for a complete controlled dataset.

Tests will also prove that irrelevant dates outside the exact lookback/backtest set do not block execution.

## Risks / Trade-offs

- **[Previously tolerated real suspensions now block a backtest]** → Fail with exact ETF/date context; add suspension support only after Vela has an authoritative trading-status source and a separate valuation contract.
- **[Historical ranges may expose incomplete calendars or metadata]** → Treat this as actionable input incompleteness rather than silently changing financial results; no database regeneration is performed by tests.
- **[Removing public options breaks external callers]** → Document the Python/CLI removal explicitly and provide the simple migration: remove `gap_detection` and obsolete strictness/threshold arguments because validation is always mandatory.
- **[Valid newly listed ETFs could be over-validated]** → Use declared `inception_date` as the only exemption boundary and add boundary tests.
- **[The local calendar source itself may be incomplete]** → Treat `TradingCalendar` as the authoritative local contract and document that upstream calendar completeness/provenance requires a separate Change.
- **[Large gap lists produce noisy errors]** → Sort deterministically, include total count, and render a bounded sample without losing machine-testable identifiers for representative gaps.

## Migration Plan

1. Add failing unit and runner tests for calendar authority, completeness, atomicity, and held-price guards.
2. Implement calendar-derived date selection and exact required-date validation before signal generation.
3. Replace equity value carry with explicit missing-endpoint errors.
4. Remove the obsolete Python configuration/export and CLI options with their tests and documentation.
5. Run focused backend/CLI tests, the complete Python gate, strict target validation, and a read-only real-data preflight.

No persistent data migration or backfill is authorized. Rollback restores tolerant execution behavior but does not modify existing stored runs.

## Open Questions

None.

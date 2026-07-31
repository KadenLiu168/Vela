## Context

`run_backtest` loads one complete, ascending price panel so the same captured inputs can be
validated, fingerprinted, used for historical signal generation, and reused by the equity curve.
`generate_historical_strategy_signals` currently rebuilds a full prefix of that panel for every
rebalance date with nested ETF lookup, while dual momentum independently filters the supplied
prefix for both trend and momentum work. For a date range with `R` rebalances, `E` ETFs, and `P`
price rows per ETF, these scans grow with the full historical prefix instead of the strategy's
declared lookback.

The strategy protocol already defines `lookback_days()` as the exact number of prior official
sessions required by a bound strategy. The backtest runner uses that value to load and validate the
required calendar coverage, so historical signal preparation can use the same contract without
reading strategy-specific configuration.

## Goals / Non-Goals

**Goals:**

- Bound each per-rebalance ETF series to at most `lookback_days() + 1` observations through the
  signal date.
- Locate slice boundaries without rescanning complete price histories for every rebalance.
- Resolve strategy dispatch and shared ETF/date indexes once per historical generation call.
- Reuse a prepared ETF series for both dual-momentum trend and momentum evaluation.
- Preserve every generated result, position, Decimal value, callback invocation, and failure
  behavior.
- Lock the scale improvement with deterministic structural regression coverage rather than a
  machine-dependent wall-clock threshold.

**Non-Goals:**

- Changing strategy formulas, rebalance-date selection, inception semantics, or look-ahead rules.
- Reducing the complete panel used by required-price validation, data snapshots, or the equity
  curve.
- Caching market data across requests or persisting derived price windows.
- Changing public function signatures, database writes, callback contracts, or transaction
  ownership.
- Optimizing checksum serialization, network fetching, or signal persistence.

## Decisions

### Resolve one bound strategy and share one internal generation path

The public single-date function will continue to resolve the configured strategy and delegate to a
shared internal helper that owns precondition, result, error, and callback semantics. Historical
generation will resolve the same bound strategy once, validate its lookback once, and call that
helper for every rebalance date.

This avoids repeated registry construction without creating a second result path. Passing a bound
strategy through a new public parameter was rejected because it would expand the public API for an
internal optimization.

### Build ETF and date indexes once

Historical generation will build:

- an `etf_id -> ETFInfo` mapping for eligibility/inception lookup; and
- one ascending trade-date sequence aligned with each ETF's existing price sequence.

For each rebalance date it will use `bisect_right` to locate the first future row, then select the
tail beginning at `max(0, end - (lookback + 1))`. Rows before an ETF's declared inception remain
excluded, and ETFs whose inception is after the rebalance date remain absent.

The production panel loader already guarantees `(etf_id, trade_date)` ascending order. Focused
precondition coverage will guard this assumption rather than sorting on every rebalance. Silently
sorting inside each invocation was rejected because it would hide a violated injected-input
contract and add avoidable work.

### Treat declared lookback as the complete strategy history contract

Every strategy invocation receives no more than its declared number of prior observations plus an
available signal-date observation. This is strategy-agnostic: dual momentum receives 127 rows for a
126-session lookback, while a zero-lookback strategy can receive only the current observation and
remains free to ignore the panel.

A strategy that needs more history must declare the larger value through `lookback_days()`. Adding
type-specific window logic to historical orchestration was rejected because it would break the
strategy-pluggability boundary.

### Prepare each dual-momentum ETF series once per signal date

The dual-momentum implementation will derive a single `etf_id -> bounded series` view from the
already bounded panel and reuse it for trend filtering and momentum scoring. It will retain its
internal ETF and defensive-asset lookup ownership.

Changing the trend or momentum helpers to cache adjusted prices globally was rejected because the
forward-adjustment anchor is signal-date-specific and the bounded series is already small.

### Verify equivalence and scale structurally

Tests will compare pre-optimization controlled expectations for weekly/monthly results, inception
boundaries, success/failure outcomes, ranks, scores, weights, and callback IDs. A long-history
regression will assert that total rows supplied to strategies are bounded by
`rebalance_count * eligible_etf_count * (lookback + 1)` and that no future row is supplied.

Wall-clock measurements may be recorded during implementation, but they will not be the sole CI
gate because shared runners make tight timing assertions flaky.

## Risks / Trade-offs

- [A strategy under-declares its required history] → Keep `lookback_days()` normative and add a
  custom-strategy regression proving the supplied bound; the strategy must correct its declaration.
- [An injected price sequence is unsorted] → Fail clearly in focused validation rather than
  producing an invalid binary-search boundary.
- [Inception filtering and tail slicing interact incorrectly] → Cover inception before, within,
  and after the candidate window, including no-future-data assertions.
- [The optimized path diverges from single-date result/persistence behavior] → Route both public
  entry points through the same internal generation helper and compare callback/results in tests.
- [A timing benchmark is unstable] → Make bounded row counts and result equivalence the required CI
  regression; treat elapsed-time evidence as supplementary.

## Migration Plan

No data or schema migration is required. Implement tests first, introduce the shared internal
generation helper and indexes, then replace repeated filtering. Rollback consists of reverting the
code change; persisted data and public contracts remain compatible.

## Open Questions

None. The existing strategy lookback and ascending-panel contracts provide the required boundary.

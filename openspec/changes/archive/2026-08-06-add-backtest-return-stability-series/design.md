## Context

Each persisted `BacktestRun` owns a strictly ordered strategy net-value curve, and benchmark-enabled runs own two curves on the same official-session axis. Summary metrics are stored as scalars, while Backtest Detail already loads these curves. The database does not persist daily returns; read-time diagnostics must therefore derive effective returns from adjacent six-decimal persisted net values rather than pretend to recover transient in-memory precision.

The current Walk-forward model keeps every OOS backtest independently inspectable. The active stitched-OOS Change adds a presentation-only compounded path with explicit portfolio resets and expressly excludes cross-window risk metrics. This Change must preserve that boundary while giving normal and individual OOS Backtest Detail pages an internal time-series view.

## Goals / Non-Goals

**Goals:**

- Derive auditable 63-effective-session rolling total return, Volatility, and Sharpe series from one persisted curve.
- Derive natural-calendar monthly and yearly compounded returns with explicit source coverage and requested-scope partial-period flags.
- Apply identical derivation semantics to strategy and both fixed benchmarks and return one typed backend-computed detail object.
- Present regime changes and calendar consistency accessibly without persisting reproducible series or calculating financial values in React.

**Non-Goals:**

- No configurable/multiple window, expanding window, rolling Alpha/Beta/Capture, parent-level WF aggregate, stitched-OOS rolling/calendar metric, new execution metric, migration, backfill, Dashboard/list/CLI expansion, or quality verdict.
- No reconstruction of holdings, seam returns, missing dates, or precision not present in persisted curves.

## Decisions

### Treat the persisted curve as the read-time authority

Add a pure core derivation function that accepts ordered dated net-value points, requested run bounds, and an optional annual risk-free rate. Require unique strictly increasing dates and positive net values. Reconstruct the effective return assigned to point `i` as `net_value[i] / net_value[i-1] - 1`. Preserve Decimal arithmetic for reconstruction, compounding, means, and variances; follow the existing Volatility/Sharpe convention of converting the square-root annualization step to float, then convert back and quantize only public Decimal results to six places.

This differs deliberately from using the original transient `daily_return`: only persisted net values are available on historical reads, so the series must be reproducible from stored evidence. Adding a daily-return column or materialized stability rows was rejected because both duplicate derivable data and require migration/backfill consistency rules. Reading current market prices or the current trading calendar was rejected because they are not the immutable source for a historical result.

### Use one fixed 63-effective-session rolling window

A rolling point exists only after 63 reconstructed effective returns, requiring 64 consecutive curve points. For a rolling result ending at curve index `i`, use returns assigned to points `i-62` through `i`, set `window_start_date` to point `i-63`, and set `trade_date` to point `i`. Publish:

- `total_return = product(1 + return) - 1`, equivalently end net value divided by start net value minus one.
- `volatility = population_std(63 returns) * sqrt(252)`.
- `sharpe_ratio = mean(return - risk_free_rate/252) / population_std(return - risk_free_rate/252) * sqrt(252)`.

Retain the existing zero-dispersion null Sharpe behavior. A curve with fewer than 64 points returns an empty rolling series with `status: insufficient_observations`, source/effective counts, and window size rather than partial-window values. A valid curve with sufficient points but no parseable `risk_free_rate` still returns rolling total return and Volatility, sets every rolling Sharpe to null, and returns `sharpe_status: unavailable_missing_risk_free_rate`; this keeps legacy detail readable. A fixed 63-session window was selected primarily because one-year OOS runs yield enough observations to reveal short-horizon intra-window regimes. It is a deliberate comparable diagnostic horizon, not a claim of statistical optimality for every multi-year backtest; 252 sessions was rejected as nearly empty for the primary OOS use case, and user configurability was rejected as unnecessary scope.

### Assign each effective return to its ending calendar period

Group each reconstructed effective return by the year/month of its ending point and compound the group. The first curve point contributes no placeholder return. For each bucket return `period`, first/last contributing dates, observation count, total return, and `is_partial`. The dates and values describe persisted curve evidence; `is_partial` has the narrower requested-scope meaning defined below and does not certify official-session data completeness.

`is_partial` describes requested calendar scope only. A month is non-partial only when the persisted run's requested `start_date` is on or before the month's first calendar date and requested `end_date` is on or after its last calendar date; a year uses the corresponding January 1/December 31 bounds. This deliberately uses immutable run bounds rather than comparing curve endpoints with calendar dates: the first or last official session may legitimately fall inside the natural period because of weekends or market holidays, so endpoint comparison alone cannot prove completeness without a trading calendar. The flag therefore MUST NOT be presented as proof that historical persisted evidence contains every official session. Periods outside the requested bounds are retained with `is_partial: true`; malformed curve ordering/value evidence still fails closed, but detecting historical trading-calendar truncation is outside this flag's semantics. Empty buckets are omitted; no zero-return month/year is fabricated. Assigning the first available net value of each bucket as a new base was rejected because it would discard the return into that session.

### Return one explicit detail-only stability object

Extend only `GET /api/backtests/{run_id}` with required `return_stability` containing `window_sessions`, source/effective counts, rolling and Sharpe statuses, strategy series, and ordered benchmark series keyed by the existing fixed benchmark identity. Each entity exposes rolling/monthly/yearly arrays with six-place Decimal strings. A legacy run with no benchmarks returns an empty benchmark collection; an empty strategy curve returns explicit empty statuses/arrays. A malformed persisted curve fails closed through the existing data-contract error path with no partial detail.

Run-creation and list responses remain unchanged. Calculating in the router or browser was rejected because financial semantics belong to typed core code. Persisting the response was rejected because it is exactly reproducible from already loaded curves and run bounds.

### Present selectable comparisons instead of dense mixed charts

Backtest Detail adds a Stability section after the existing equity curve. Use one metric selector for Rolling Return, Rolling Volatility, and Rolling Sharpe; the selected chart compares strategy and available fixed benchmarks on the same metric scale and exposes a table/text fallback. Monthly and yearly views use an entity selector and accessible table/heatmap cells containing exact API values, period, count, and partial marker. Do not overlay the three differently scaled rolling metrics on one axis or add nested card grids.

An OOS backtest opened from Walk-forward uses this same route and behavior. The Walk-forward parent detail and stitched curve receive no stability section or derived values.

## Risks / Trade-offs

- [Reconstructed returns can differ slightly from transient in-memory returns] → State that read-time series derive from persisted six-decimal net values and lock independent tests to that evidence.
- [A 63-session window is noisier than a full year] → Position it as an OOS-oriented short-horizon diagnostic, label the window explicitly, expose dates/counts, and avoid claims that it is universally optimal or statistically significant.
- [`is_partial` cannot prove historical official-session completeness] → Define it strictly as requested calendar scope, expose contributing dates/counts separately, avoid curve-endpoint heuristics that misclassify holidays/weekends, and do not label it as a data-completeness guarantee.
- [Legacy parameter snapshots may lack risk-free rate] → Preserve rolling return/volatility and expose an explicit unavailable Sharpe status instead of failing the whole detail or assuming zero.
- [Three entities and several series can overwhelm the page] → Use selectors plus accessible tables and preserve a single clear chart at a time.
- [Stitched-OOS reset semantics must be stable before integration] → Apply only after `add-stitched-oos-equity-curve` completes, then rebaseline its final exclusion contract plus the limited shared API schema/client files and Walk-forward regressions; the primary endpoints and pages remain distinct.

## Migration Plan

1. Complete the stitched-OOS Change and re-read its final reset/exclusion contracts plus shared API schema/client integration points.
2. Add pure derivation tests and implementation for curve validation, reconstructed returns, 63-session windows, legacy risk-free behavior, calendar buckets, and requested-scope partial flags.
3. Integrate the detail-only typed API object and exact OpenAPI/error tests without changing persistence or list/run payloads.
4. Add the Backtest Detail Stability presentation and deterministic unit/browser coverage, then run complete Python/Web and strict OpenSpec gates plus independent semantic review.

Rollback removes the derived detail field and Web section; persisted runs, benchmarks, curves, and databases are unchanged.

## Open Questions

None. The window is fixed at 63 effective sessions for an OOS-oriented short-horizon diagnostic, persisted net values are authoritative for derived values, calendar returns use ending-date assignment, `is_partial` reports requested calendar scope rather than official-session completeness, and stitched OOS is excluded.

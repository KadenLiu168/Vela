## Context

`WalkForwardRunner` already searches each training interval in an in-memory SQLite backup, persists only selected OOS runs through the caller-owned source transaction, and attaches two fixed benchmark comparisons to every OOS result. `WalkForwardReport` retains train Sharpe, OOS CAGR/Sharpe/maximum drawdown and benchmark differences, but only aggregates CAGR and Sharpe; parameter stability is a raw value listing, and the main specification still mentions the removed optional baseline.

The current default configuration creates three non-overlapping one-year OOS windows, but the window model also permits overlaps or gaps when `step_years` differs from `test_years`. Every OOS backtest independently initializes net value, cash and holdings, so its curve is not a continuation of the prior window.

## Goals / Non-Goals

**Goals:**

- Turn the CLI report into an explicit evidence report covering return, risk, benchmark-relative consistency, IS/OOS degradation and parameter stability.
- Preserve metric-specific null handling and expose the number of observations behind every statistic or rate.
- Mark evidence with fewer than three valid OOS windows as insufficient without suppressing results or inventing a pass/fail policy.
- Add an integration contract that exercises real metric calculation and persistence using a test-owned SQLite database.

**Non-Goals:**

- No automatic strategy approval, rejection, composite score or configurable threshold framework.
- No continuous or linked OOS equity curve, cross-window holdings, boundary turnover or transition-cost simulation.
- No Walk-forward persistence model, HTTP API, Web page or default-database execution.
- No new performance formulas such as Sortino, Calmar, Tracking Error or Information Ratio.

## Decisions

### Extend window results without changing OOS execution

Add OOS total return and volatility to `WalkForwardWindowResult` alongside the existing CAGR, Sharpe and maximum drawdown. Populate all five values from the selected `run_backtest` result; benchmark calculation and caller transaction ownership remain unchanged.

Alternative considered: recalculate metrics from persisted OOS curves inside the report. Rejected because the runner already owns authoritative calculated values, and duplicate calculation would create a second metric path.

### Return typed summaries with metric-local validity

For each of total return, CAGR, Sharpe, maximum drawdown and volatility, produce `mean`, `median`, `min`, `max`, population standard deviation, `window_count`, `valid_count` and `evidence_status`. Nulls are excluded only from their own metric. With no valid value, all descriptive statistics are null and `valid_count` is zero. `evidence_status` is `sufficient` when `valid_count >= 3`, otherwise `insufficient_evidence`; this status records only whether the operational minimum count was met and does not claim statistical independence or strategy validity.

Maximum drawdown retains its public negative-number convention. Consequently `min` is the deepest drawdown; the formatted report labels it `worst` rather than relying on the reader to infer sign direction.

Alternative considered: discard any window containing one null metric. Rejected because it would silently remove valid evidence for unrelated metrics.

### Define rates from total return and explicit denominators

The positive-window rate is the number of non-null OOS total returns strictly greater than zero divided by the number of non-null OOS total returns. For each fixed benchmark, the outperformance rate is the number of non-null strategy-minus-benchmark total-return differences strictly greater than zero divided by their non-null count. Zero differences are ties, not wins. Each rate exposes numerator, denominator, value, `window_count`, `valid_count` and evidence status. When the denominator is zero, numerator and denominator are both zero, value is null and evidence is insufficient.

Use total return rather than CAGR because the question is whether the strategy gained or beat its benchmark over that concrete OOS interval. Continue to summarize both total-return and CAGR differences for magnitude using the same metric-local standard summary, including total/valid counts and evidence status.

### Summarize generalization without unstable ratios

For every window with both values, compute `train_sharpe - oos_sharpe`; positive values mean degradation from IS to OOS. Aggregate the gaps with the standard summary structure. Do not compute a ratio because zero and negative OOS Sharpe make it unstable and hard to interpret.

### Quantify parameter stability with simple categorical statistics

For each searched parameter, report canonical value frequencies, adjacent-window transition count, comparison count and transition rate. Resolve each selected dot-path from the validated strategy configuration's JSON-mode data rather than retaining the parameter generator's raw Python value; encode that effective scalar as canonical JSON for frequency keys and transition comparison. Windows remain in chronological order. Fewer than two comparable windows yields no transition rate.

Alternative considered: entropy or a cross-parameter stability score. Rejected because parameters have heterogeneous types and no agreed distance function; a composite score would imply precision not supported by three windows.

### Keep every OOS window economically isolated

The report SHALL NOT emit a continuous OOS curve or compute path metrics across window boundaries. Independent runs reset cash and holdings and do not charge turnover from the previous window's ending portfolio into the next window's selected configuration. The current window model can also overlap or leave gaps. A genuine continuous OOS simulation therefore requires a separate execution-model Change.

### Validate through the production path on test-owned data

Keep focused pure aggregation tests, then add one deterministic integration test using an Alembic-prepared file-backed SQLite database. Seed exactly one active `SSE:510300`, the other minimal valid strategy universe, and complete official-session/price inputs from the maximum valid-candidate lookback envelope through the configured end date. Use a deliberately small parameter space and run the real `WalkForwardRunner`/`run_backtest` path. Assert literal controlled values for each window's five metrics and representative aggregate/generalization/dual-benchmark statistics, plus exact counts/rates, deterministic OOS identities and parameter stability. Exercise failure through the CLI managed-session boundary and assert every source-side signal, position, run, strategy curve, benchmark and benchmark-curve row rolls back. Never target `vela.db`.

## Risks / Trade-offs

- [Exactly three valid OOS windows meet the operational minimum but remain weak and may overlap] → label them `sufficient` only in the count-threshold sense, expose counts, and never imply independence or translate the report into automatic approval.
- [Negative maximum-drawdown values make generic min/max labels confusing] → retain the API convention but label the minimum as the worst drawdown in formatted output.
- [Expanded report structures can break tests or internal callers] → update typed dataclasses and all construction sites together; this Change does not create a public HTTP contract.
- [Integration fixtures could become slow] → use a minimal valid universe, narrow parameter space and only the sessions required for deterministic windows and lookback.
- [Users may interpret window-linked returns as continuous performance] → do not generate a linked index in this Change and state the isolation explicitly in the report/specification.

## Migration Plan

No database or external API migration is required. Update the in-memory report types, runner mapping, formatter and tests atomically. Rollback restores the former report fields and aggregation without touching persisted OOS backtests.

## Open Questions

None. Automatic pass/fail, continuous OOS simulation and report persistence are explicitly deferred.

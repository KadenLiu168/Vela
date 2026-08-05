## Context

Normal and selected Walk-forward OOS backtests already persist one strategy curve and exactly two fixed benchmark curves on the same ordered official-session axis. `calculate_active_risk_metrics` fails on any effective-date mismatch and provides a proven pattern for aligned comparison metrics, while `BacktestBenchmark` owns benchmark-relative TE/IR. The missing metrics are therefore scalar derivatives of existing authoritative evidence, but their financial names are easy to overstate: `SSE:510300` is an ETF proxy for CSI 300 rather than an official total-return index, and the equal-weight benchmark is not a CAPM market factor.

The Change must preserve caller-owned transaction behavior, legacy readability, six-decimal public precision, evidence-only Walk-forward reporting, and the existing no-fill/no-truncation calendar policy. The in-progress stitched-OOS Change is completed first operationally, but this Change never uses the stitched curve because each OOS run remains the owner of its own relative metrics.

## Goals / Non-Goals

**Goals:**

- Add one deterministic CAPM proxy-regression result for the strategy versus `csi_300_buy_hold` and one deterministic capture result for each fixed benchmark.
- Keep every calculation auditable through exact input alignment, explicit risk-free-rate and annualization rules, observation counts, stable version markers, nullable invalid boundaries, and fixed-value tests.
- Persist new-run values atomically, preserve legacy nulls, and expose the same semantic result through reports, HTTP, Web, and Walk-forward evidence.
- Retain per-window and aggregate evidence without turning Alpha, Beta, R-squared, or Capture into an automatic quality verdict.

**Non-Goals:**

- No multifactor model, significance test, confidence interval, rolling Alpha/Beta/Capture, configurable market factor, official CSI index feed, benchmark intersection, filling, or regression over stitched OOS windows.
- No CAPM naming for `equal_weight_monthly`; it receives capture metrics only.
- No backfill, default-database migration, Dashboard/list expansion, score, threshold, ranking, or pass/fail result.

## Decisions

### Reuse one strict aligned-return boundary

Introduce an immutable `BenchmarkRegimeMetrics` result and a pure public calculation function receiving strategy points, benchmark points, annual `risk_free_rate`, and the benchmark key. Exclude each curve's initial placeholder and require the remaining ordered dates to match exactly before any calculation. A mismatch raises the same explicit contract error style as active-risk calculation; the function never intersects, sorts, truncates, or fills data.

One comparison helper was selected over separate CAPM and capture entry points because alignment, effective-observation extraction, precision, and evidence counts must not drift. Reusing TE/IR outputs was rejected because active returns alone discard the benchmark regime sign and market variance needed here.

### Qualify CAPM to the CSI 300 ETF proxy

For `csi_300_buy_hold`, set `rf_daily = risk_free_rate / 252`, `S = strategy_return - rf_daily`, and `M = benchmark_return - rf_daily` across all aligned effective observations. With population moments retained unquantized:

- `beta = covariance(S, M) / variance(M)`.
- `alpha_daily = mean(S) - beta * mean(M)`.
- `alpha_annualized = (1 + alpha_daily) ^ 252 - 1`.
- `r_squared = covariance(S, M)^2 / (variance(S) * variance(M))`.

Quantize only final public Decimal values to six places. Fewer than two observations or zero market variance makes Alpha, Beta, and R-squared null. Zero strategy variance with non-zero market variance permits Beta but makes R-squared null. A daily Alpha at or below `-1` makes annualized Alpha null. Preserve `capm_observation_count` even when a result is undefined.

For `equal_weight_monthly`, every CAPM field and count is null. Returning an equal-weight regression under a different label was rejected because it would create a second model without the requested CAPM meaning. Arithmetic `alpha_daily * 252` was rejected in favor of a compounded annual rate whose label explicitly says `252D compounded`; tests independently lock this choice.

### Define capture from benchmark-classified monthly geometric returns

After strict daily-date alignment, group both return series by the same calendar `(year, month)` keys in chronological order and compound every observed daily return in each bucket as `monthly_return = product(1 + daily_return) - 1`. Do not resample, intersect, fill, or import observations outside the run. A first or last partial calendar month remains an observed month bucket using exactly the aligned official sessions owned by the run; dropping it or completing it with out-of-run data was rejected because either choice would silently discard or invent owned evidence.

Select monthly buckets whose benchmark monthly return is strictly above zero for Up Capture and strictly below zero for Down Capture; exclude zero-benchmark months. For one selected regime of `n` months, calculate the strategy and benchmark geometric mean monthly returns as `product(1 + selected_monthly_return) ^ (1 / n) - 1`, then publish strategy geometric mean divided by benchmark geometric mean. This is a monthly geometric-average capture convention: it preserves compounding without applying the CAPM-specific `252/n` annualization to a participation ratio. Retain unquantized intermediates and quantize final capture ratios to six places.

Return null for an empty regime or when any constituent daily return or resulting monthly return in a selected bucket is at or below `-1`. For every otherwise valid nonempty up/down regime, the benchmark geometric mean is respectively strictly positive/negative and therefore non-zero by construction. Always retain `up_observation_count` and `down_observation_count`, where each count is the number of selected calendar-month buckets rather than daily sessions. Do not multiply ratios by 100 in storage/API; Web and reports label them as monthly capture ratios and may format `1.0` as `100% capture` without changing the value. Arithmetic-mean capture was rejected because it would not preserve compounding, unannualized cumulative-return division was rejected because it would mix comparison-horizon length into the ratio, and daily `252/n` annualization was rejected because monthly industry interpretation is more important than compatibility with a daily conditional-return library convention.

### Persist comparison fields on benchmark children

Add nullable `capm_alpha`, `capm_beta`, `capm_r_squared`, `capm_observation_count`, `up_capture_ratio`, `up_capture_observation_count`, `down_capture_ratio`, and `down_capture_observation_count` columns to `BacktestBenchmark`. This keeps every comparison beside its benchmark identity and existing TE/IR. Enforce in calculation/serialization that CAPM fields are populated only for `csi_300_buy_hold`; database nullability preserves legacy rows and does not attempt a brittle cross-column SQL constraint.

Record `benchmark_regime_metrics_v1` in the run's parameter snapshot for every benchmark-enabled run that reaches this metric family. Walk-forward training trials skip benchmarks and therefore do not calculate or version it. Storing fields on `BacktestRun` was rejected because capture belongs to two separate comparisons and proxy ownership would become implicit.

### Expand Walk-forward evidence with a new document version

Each selected OOS window reads the fields from its owned persisted benchmark rows. Aggregate every Alpha/Beta/R-squared/Capture metric separately with the existing mean/median/min/max/population-standard-deviation, total-window count, valid-count, and evidence-status contract. Observation counts remain per-window evidence and are not averaged as performance metrics.

New runs persist `wf_evidence_v2`; query and API validators support both legacy `wf_evidence_v1` and new `v2`, fail closed on an unsupported/corrupt version, and never synthesize missing legacy metrics. `v2` extends the existing evidence rather than changing established metric meanings. Mutating `v1` in place was rejected because its strict versioned schema is already persisted.

### Expose stored values without recalculation

Reports, API routers, and React serialize/display persisted comparison values and counts; they do not rerun regression or capture arithmetic. Backtest Detail places proxy CAPM only in the CSI 300 group and monthly capture in both named benchmark groups, with explicit `252D compounded` Alpha, proxy, monthly-ratio, and selected-month-count language. Walk-forward Detail shows per-window and aggregate evidence and preserves `insufficient_evidence` rather than applying thresholds.

## Risks / Trade-offs

- [Users may read proxy Alpha as universal manager skill] → Include `CSI 300 ETF proxy` in labels and help text and do not expose an unqualified strategy-level Alpha field.
- [One-year OOS regressions can be noisy] → Publish observation counts and R-squared, retain evidence statuses, and avoid significance or pass/fail claims.
- [Capture ratios can be extreme near a zero denominator] → Return null only for an exactly zero unquantized denominator, expose counts, and avoid clipping or caps that would hide evidence.
- [A run may begin or end inside a calendar month] → Treat each actually observed edge bucket as one month, label counts as observed/selected months, and never fetch, fill, or infer returns outside the owned run interval.
- [Sequential metric Changes can proliferate versions] → Give this family its own `benchmark_regime_metrics_v1` marker and explicitly advance the versioned WF evidence document while retaining legacy readers.
- [Schema/API/Web edits overlap the stitched-OOS worktree] → Complete and independently verify `add-stitched-oos-equity-curve` before applying this Change.
- [`add-tail-distribution-risk-metrics` consumes this Change's `wf_evidence_v2`] → Complete and independently verify this Change before applying the downstream tail-distribution Change that advances evidence to `v3`.

## Migration Plan

1. Complete the active stitched-OOS Change, then add fixed numerical and boundary tests for daily CAPM and monthly geometric capture, including partial edge-month behavior.
2. Add nullable benchmark columns through one Alembic revision and validate upgrade/downgrade plus legacy preservation on test-owned file-backed SQLite.
3. Integrate calculation, persistence, reports, and `wf_evidence_v2` inside current caller-owned transactions.
4. Extend typed HTTP and Web surfaces and run focused, full Python, full Web, strict OpenSpec, migration, and independent semantic review gates; only after this Change passes those gates may `add-tail-distribution-risk-metrics` advance `wf_evidence_v2` to `v3`.

Rollback removes the new UI/API fields and calculation path, downgrades only the new nullable columns, and keeps all pre-existing strategy, benchmark, curve, and evidence records. No production/default database is migrated by validation.

## Open Questions

None. The Change fixes the market proxy, daily CAPM annualization, monthly geometric capture formula, partial-edge-month behavior, alignment, count units, persistence owner, evidence version, and legacy behavior.

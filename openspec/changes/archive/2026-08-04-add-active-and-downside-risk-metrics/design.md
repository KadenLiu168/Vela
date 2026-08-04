## Context

Vela persists five strategy metrics and the same five metrics for `equal_weight_monthly` and `csi_300_buy_hold`. Strategy and benchmark curves share one validated official-session axis, so daily active returns can be calculated without an additional alignment or fill policy. Existing CAGR is a 365-calendar-day geometric endpoint return, while volatility and Sharpe use effective daily returns and 252-day arithmetic annualization; this Change must preserve that contract.

The selected OOS runs produced by Walk-forward are ordinary persisted backtests with fixed benchmarks. This Change is sequenced after `strengthen-walk-forward-evaluation-contract`, allowing the new metrics to extend its typed evidence summaries without introducing a second report model.

## Goals / Non-Goals

**Goals:**

- Add one exact, shared calculation path for Sortino, Calmar, longest drawdown duration, Tracking Error and Information Ratio.
- Persist calculated values at run time for strategy and benchmarks, with explicit metric-version provenance and legacy null compatibility.
- Expose the values consistently through API, CLI/export, Backtest Detail and selected-OOS evidence.
- Preserve existing formulas, values, transaction behavior, official-session completeness and missing-price fail-fast semantics.

**Non-Goals:**

- No CAGR conversion to a 252-session formula and no reconstruction of Sharpe from CAGR.
- No Alpha, Beta, capture ratios, VaR/CVaR, factor attribution or dynamic risk-free-rate provider.
- No historical metric backfill and no query-time recalculation for legacy runs.
- No Dashboard expansion, continuous OOS curve or automatic strategy pass/fail.

## Decisions

### Centralize immutable metric result types and six-decimal outputs

Add focused immutable result types and calculation functions beside the existing equity-curve metrics. Follow the current public surface by exporting `StrategySortinoRatio`, `StrategyCalmarRatio`, `StrategyLongestDrawdownDuration`, `ActiveRiskMetrics` and their `calculate_strategy_sortino_ratio`, `calculate_strategy_calmar_ratio`, `calculate_strategy_longest_drawdown_duration`, and `calculate_active_risk_metrics` functions from `vela_core`. The functions respectively accept `(points, *, risk_free_rate)`, `(annualized_return, maximum_drawdown)`, `(points)`, and `(strategy_points, benchmark_points)` and return the matching immutable result type. Reuse them for strategy and both benchmarks without changing existing public signatures.

All means, variances, square roots, annualization factors, downside deviations and active-risk denominators remain unquantized during one calculation. Quantize only the final published Decimal fields to six places. In particular, Information Ratio uses the unquantized annualized Tracking Error, not the already quantized TE field. If the final TE quantizes to `0.000000`, IR is null so the public denominator and ratio do not contradict each other. Duration counts and dates remain typed integers/dates.

Alternative considered: calculate new metrics independently in benchmark, API or frontend code. Rejected because it would create divergent formulas and make historical audit impossible.

### Sortino uses the recorded risk-free rate as MAR

From effective observations `points[1:]`, define `target_daily = risk_free_rate / 252`, `excess_i = daily_return_i - target_daily`, and `downside_i = min(excess_i, 0)`. Annualized downside deviation is `sqrt(mean(downside_i^2)) * sqrt(252)` across all effective observations, not only negative observations. Sortino is `mean(excess_i) * 252 / annualized_downside_deviation`; only that final ratio is quantized.

The controlled vector uses annual `risk_free_rate=0.0252` and effective daily returns `[0.0101, -0.0049, 0.0201]`, producing excess returns `[0.0100, -0.0050, 0.0200]` and Sortino `45.825757`.

Return no Sortino with fewer than two effective observations or zero downside deviation. The annual risk-free value is already captured in `parameters_json`; automatic market updates would make the same configuration non-deterministic and are excluded.

Alternative considered: MAR zero. Rejected because the user selected risk-free MAR and it aligns with current Sharpe excess-return semantics.

### Calmar preserves calendar-time CAGR

Calmar is `annualized_return / abs(max_drawdown)`, using the already published six-decimal calendar-time CAGR and deepest negative maximum-drawdown result as its inputs. It does not recalculate either input from the curve; the division remains unquantized until the final Calmar is quantized. Return no value when CAGR is null or maximum drawdown is zero. A negative CAGR produces a negative Calmar.

Alternative considered: convert CAGR to 252 sessions. Rejected because maximum drawdown is not annualized and the repository deliberately distinguishes calendar-time CAGR from daily-return risk statistics.

### Longest drawdown duration follows official-session intervals

Scan ordered net values by high-water mark. While the curve is not underwater, an observation equal to the current high-water value replaces the peak anchor, so a later drawdown starts from the last equal high immediately preceding the underwater observation. Recovery occurs on the first later point whose net value is at least that peak; an equal-value recovery point becomes the anchor for any following interval. Duration is the difference between recovery and peak indices; an unrecovered interval ends at the final point and has `recovery_date=None`. Retain the interval's peak date, earliest deepest trough date and optional recovery date. Select the greatest duration, breaking ties by earliest peak then earliest trough. A curve that never goes underwater returns duration zero with null dates. Thus `[1.0@d1, 1.0@d2, 0.9@d3, 1.0@d4]` returns peak `d2`, trough `d3`, recovery `d4`, and duration `2`.

This duration interval can differ from the interval containing the numerically deepest maximum drawdown; both are valid but answer different questions.

### Active metrics require exact date identity

For each benchmark, exclude both initial placeholder returns and require the strategy and benchmark effective observations to have exactly identical ordered dates. A mismatch raises a domain calculation error rather than shortening or filling either series.

Define `active_i = strategy_daily_return_i - benchmark_daily_return_i`, raw `TE = population_std(active_i) * sqrt(252)`, and `IR = mean(active_i) * 252 / raw_TE`. With fewer than two active observations both values are null. Zero active dispersion yields TE zero and IR null; a non-zero raw TE that quantizes to `0.000000` also yields null IR. For active returns `[0.002, -0.001, 0.005]`, the unquantized annualized TE is approximately `0.038884444190`; the published TE is `0.038884` and IR is `12.961481`. Computing IR from published TE would produce `12.961629` and is prohibited.

### Preserve pre-signal benchmark fail-fast and caller transaction ownership

Keep benchmark identity, official-session price completeness and benchmark-curve construction before strategy signal generation, preserving the existing missing-input failure with no signal artifacts. After signals and the strategy curve exist, calculate strategy absolute metrics and compare its effective dates with each already-built benchmark curve for TE/IR before `persist_backtest_result`.

An active-metric alignment failure can occur after signal rows have been flushed into the caller's uncommitted session. `run_backtest` does not commit or roll back the caller's transaction; the CLI/API managed-session boundary and the Walk-forward source transaction roll the whole attempt back. Tests must distinguish this late rollback contract from the earlier benchmark-input failure that occurs before signal generation.

Normal success and partial runs, selected OOS runs and benchmark-skipping training trials all calculate strategy Sortino, Calmar and duration and record `performance_metrics_v1`. Benchmark-enabled paths additionally calculate benchmark absolute metrics and TE/IR. Training writes remain confined to the isolated in-memory snapshot and never persist to the source database.

### Persist explicit nullable columns and one metric version

Add nullable strategy columns on `backtest_run`: `sortino_ratio`, `calmar_ratio`, `longest_drawdown_duration_sessions`, `longest_drawdown_peak_date`, `longest_drawdown_trough_date`, and `longest_drawdown_recovery_date`. Add the same absolute fields plus `tracking_error` and `information_ratio` on `backtest_benchmark`.

Every new run that reaches expanded strategy metric calculation writes duration zero when no drawdown exists and adds `performance_metric_version: "performance_metrics_v1"` to its parameter snapshot, including success, partial, selected OOS and isolated training runs. Legacy rows remain null and are not confused with a verified zero. Benchmark rows inherit the parent run's version.

Alternative considered: a flexible metrics JSON column. Rejected because the current model uses typed columns, these metrics are stable public fields, and typed constraints/API schemas are easier to audit.

### Propagate persisted values without recomputation

The API, CLI/export and Backtest Detail read stored values. Strategy TE/IR appear inside each benchmark comparison because they are defined relative to that benchmark. Labels disclose `Sortino (rf MAR, 252D)`, `Calmar (calendar CAGR / |MaxDD|)`, `Tracking error (252D)` and `Information ratio (252D)`. Backtest Detail shows duration sessions and dates; Dashboard remains unchanged. Browser QA covers the supported desktop and narrow viewports so added metric groups remain readable, correctly owned and unclipped without changing existing keyboard or semantic structure.

After the first Change, Walk-forward copies new selected-OOS fields into its window evidence. It aggregates strategy Sortino, Calmar and duration with the established valid-count/evidence rules, and aggregates each benchmark's TE/IR separately. It still does not join OOS curves.

### Migrate and verify without touching the default database

Use one Alembic revision with nullable additions and a downgrade that removes only those additions. Migration and end-to-end tests use Alembic-prepared file-backed SQLite databases. Core controlled vectors own formula exactness; runner/persistence tests own atomic storage; API/CLI/Web tests own transport and presentation.

## Risks / Trade-offs

- [Sortino definitions vary across libraries] → lock MAR, denominator population and all-observation lower-partial-moment semantics in fixed-vector tests and labels.
- [Quantizing TE before IR changes the published result] → retain unquantized intermediates, lock both controlled values, and make sub-resolution TE produce null IR.
- [Longest duration may be mistaken for deepest drawdown interval] → use distinct field names and expose peak/trough/recovery dates for the selected longest interval.
- [A benchmark date mismatch could hide data defects] → fail rather than intersect, forward-fill or shorten the series.
- [Moving benchmark work behind strategy execution could weaken existing fail-fast] → keep benchmark input/curve construction before signals and calculate only active comparison after the strategy curve.
- [Many nullable columns enlarge response/model surfaces] → follow existing typed metric fields; do not introduce speculative generic storage.
- [Legacy rows contain null while new flat runs contain duration zero] → preserve this distinction in migration, API and UI tests.
- [Second Change depends on the first report contract] → Apply and stabilize `strengthen-walk-forward-evaluation-contract` before updating Walk-forward evidence here.

## Migration Plan

1. Add nullable columns using Alembic and verify upgrade/downgrade on a file-backed SQLite database containing legacy runs and benchmark rows.
2. Deploy calculation and persistence together so normal success/partial, selected OOS and isolated training runs write their supported values and `performance_metrics_v1` within their existing transaction boundary.
3. Deploy API/CLI/Web consumers that accept both new values and legacy nulls.
4. Rollback application code before downgrading; downgrade drops only the new columns and leaves existing five metrics, curves and runs intact.

## Open Questions

None. MAR, persistence, legacy handling, metric version and excluded advanced metrics are fixed by the approved design.

## Context

Vela calculates summary and active/downside metrics from each strategy or fixed benchmark curve's effective daily returns, excluding the initial zero-return placeholder. It persists scalar metrics for normal and selected Walk-forward OOS runs, retains the owning OOS records behind Walk-forward history, and reports aggregate evidence with metric-local valid counts rather than strategy verdicts. No current metric describes a historical loss quantile, conditional tail severity, distribution asymmetry, or excess tail weight.

This Change follows `add-benchmark-regime-performance-metrics` semantically. That prerequisite introduces `wf_evidence_v2`; tail-risk history advances it to `wf_evidence_v3` while retaining legacy readers. The Change must preserve current six-decimal conventions, caller-owned atomicity, strict benchmark ownership, legacy nulls, and no writes to the user's default database during validation.

## Goals / Non-Goals

**Goals:**

- Add one small historical one-day loss family: 95% VaR, 95% CVaR, bias-corrected sample Skewness, and bias-corrected Fisher excess Kurtosis.
- Lock sample threshold, sign, rank, tail membership, correction, constant-series, precision, and evidence-count semantics with independent numerical oracles.
- Calculate and persist the same absolute metrics for strategy and each fixed benchmark and expose them consistently across reports, HTTP, Web, and Walk-forward evidence.
- Make limited samples explicit without converting risk evidence into a threshold on strategy quality.

**Non-Goals:**

- No parametric/normal/Cornish-Fisher/GPD VaR, multi-day scaling, stressed Expected Shortfall, liquidity horizon, scenario generation, forecast, regulatory-capital claim, rolling tail metric, stitched-OOS tail metric, configurable confidence level, or significance test.
- No historical backfill, default-database migration, Dashboard/list expansion, score, ranking, alert, or pass/fail result.

## Decisions

### Reuse effective daily returns and require 100 observations for publication

Add an immutable `TailDistributionRiskMetrics` result and one pure public function receiving a sequence of equity-curve points. Exclude the first placeholder and use the existing point `daily_return` values during execution for both strategy and benchmarks. Retain `observation_count` for every result.

Set `evidence_status` to `sufficient` only for at least 100 effective observations; otherwise publish all four metrics as null, set `tail_observation_count` to `ceil(0.05 * observation_count)` (zero for no observations), and set `insufficient_evidence`. The retained tail count is the cardinality implied by the fixed rank rule, not a claim that a withheld VaR/CVaR value was published from that tail. One hundred observations ensures the fixed 5% historical tail contains at least five observations while remaining available for typical one-year OOS windows. Calculating unstable values from a handful of returns was rejected; silently omitting counts was rejected because users need to distinguish unavailable evidence from a zero loss.

This is an evidence-publication threshold, not a strategy-quality threshold. It does not produce a pass/fail result and is independent of the existing three-window WF aggregation sufficiency rule.

### Use nearest-rank historical loss with fixed tail cardinality

For sufficient evidence of size `n`, sort unquantized daily returns ascending and set `tail_count = ceil(0.05 * n)`. The VaR cutoff return is the element at zero-based index `tail_count - 1`; the CVaR tail is exactly the first `tail_count` sorted observations. Publish:

- `historical_var_95 = max(0, -cutoff_return)`.
- `historical_cvar_95 = max(0, -mean(worst tail_count returns))`.

Quantize only final Decimal values to six places. Fixed cardinality means equal observations beyond the cutoff are not added, although tied values make their identity irrelevant. CVaR SHALL be greater than or equal to VaR under this positive-loss convention; a violation is a contract error. Linear percentile interpolation was rejected because it creates a synthetic return; including every cutoff tie was rejected because it makes tail count data-dependent and harder to audit. Raw negative-return publication was rejected in favor of labels and values that both express positive loss magnitude.

### Use explicit bias-corrected Fisher shape statistics

For the same sufficient return set, calculate population central moments `m2`, `m3`, and `m4` without intermediate quantization. If `m2` is zero, publish both shape metrics as null. Otherwise publish:

- Adjusted Fisher-Pearson skewness `G1 = sqrt(n(n-1)) / (n-2) * (m3 / m2^(3/2))`.
- Bias-corrected Fisher excess kurtosis `G2 = (n-1)/((n-2)(n-3)) * ((n+1) * (m4/m2^2 - 3) + 6)`.

Quantize final values to six places and label kurtosis as `Excess kurtosis (normal = 0)`. Relying on library defaults was rejected because bias and Fisher/Pearson defaults differ; the implementation may reuse existing NumPy primitives but the formula and independent oracle remain authoritative. With the 100-observation publication threshold, the formulas' smaller mathematical minimums do not create separate public states.

### Persist absolute metrics with each curve owner

Add nullable `historical_var_95`, `historical_cvar_95`, `return_skewness`, `return_excess_kurtosis`, `distribution_observation_count`, and `tail_observation_count` fields to both `BacktestRun` and `BacktestBenchmark`. Counts are nullable only for legacy rows; newly calculated rows always store non-negative counts even when metrics are null. Evidence status is derived deterministically from the count and fixed threshold rather than stored as a redundant mutable string.

Record `tail_distribution_metric_version: tail_distribution_metrics_v1` in every normal success/partial, selected OOS, and isolated training calculation snapshot. Training trials calculate strategy-only metrics in their isolated snapshot and persist nothing to the source database, matching existing expanded-metric behavior. A separate distribution table was rejected because these are one-to-one scalar attributes of an existing curve owner.

### Advance Walk-forward history to v3

Each selected OOS window retains strategy and both benchmark distribution values/counts from its owned records. Aggregate each entity/metric independently using the existing mean, median, minimum, maximum, population standard deviation, total-window count, valid count, and evidence-status structure. These aggregates describe variation across independent per-window metric estimates; they are not VaR/CVaR or shape statistics calculated from a combined or stitched return distribution. Nulls do not contribute and valid zeros do. The UI/report states this cross-window interpretation and does not label minimum or maximum as universally “worst”; the positive-loss metrics and signed shape metrics have different interpretations.

New runs persist `wf_evidence_v3`, defined as valid `v2` evidence plus tail-distribution per-window and aggregate groups. Persistence, query, and API support valid legacy v1/v2 documents and strict v3, reject unsupported/corrupt documents, and never fabricate missing old fields. Creating another incompatible `v2` was rejected, which is why `add-benchmark-regime-performance-metrics` is a prerequisite.

### Expose stored semantics without recalculation or regulatory language

Backtest reports, API, and React read persisted values and derive only the fixed evidence-status label from counts. Backtest Detail presents strategy and both benchmark metrics with `1D historical loss`, `95%`, observation/tail counts, and `normal = 0` language; when evidence is insufficient, it explains that the visible tail count is the rank-rule cardinality while metric publication still requires at least 100 effective observations. Walk-forward Detail presents per-window and aggregates with metric-local evidence counts and identifies aggregates as cross-window descriptive summaries rather than combined-distribution risk estimates. Routers and browsers never sort returns or recompute metrics.

## Risks / Trade-offs

- [Historical VaR/CVaR can understate unseen losses] → Label them as observed one-day historical evidence and pair them with counts; make no forecast or capital claim.
- [A 100-observation threshold hides mathematically calculable small-sample values] → Return explicit counts/status and prefer reliable absence over deceptively precise tails.
- [Positive-loss VaR differs in sign from some libraries] → Lock names, formulas, invariant `CVaR >= VaR >= 0`, and UI labels in tests.
- [Skewness and kurtosis are sensitive to outliers] → Present them as descriptive statistics, retain MaxDD/other metrics, and avoid thresholds or rankings.
- [A mean or range of per-window VaR/CVaR values can be mistaken for one combined strategy risk estimate] → Explicitly label Walk-forward aggregates as descriptive statistics across independent window estimates and never calculate them from the stitched curve.
- [A non-zero tail count beside withheld insufficient metrics can look contradictory] → Explain that the count is the fixed-rank tail cardinality while the 100-observation publication threshold still governs metric availability.
- [This Change depends on the benchmark-regime evidence version] → Verify the prerequisite is complete before Apply and advance v2 to v3 with backward-compatible readers.

## Migration Plan

1. Complete and verify `add-benchmark-regime-performance-metrics`, then rebaseline current models, evidence versions, API, and Web fields.
2. Add independent-oracle and boundary tests for the pure metric family and implement the smallest public calculation path.
3. Add nullable strategy/benchmark columns in one Alembic revision and validate legacy upgrade/downgrade on test-owned file-backed SQLite.
4. Integrate execution, persistence, reports, `wf_evidence_v3`, typed HTTP, and Web presentation inside existing ownership/transaction boundaries.
5. Run focused, complete Python/Web, strict OpenSpec, migration, and independent semantic-review gates.

Rollback removes the new surfaces and calculation path and downgrades only the nullable columns introduced here. Pre-existing runs/evidence remain unchanged and readable; no default database is migrated by validation.

## Open Questions

None. Confidence level, horizon, minimum evidence, rank rule, tail cardinality, sign, bias correction, ownership, versions, and legacy behavior are fixed.

## Why

Maximum drawdown and Volatility do not describe the observed loss quantile, average severity beyond that quantile, or asymmetry and tail weight of daily returns. Vela needs a small, explicitly historical distribution-risk family so users can inspect these characteristics without mistaking a parametric estimate or a regulatory capital measure for observed backtest evidence.

## What Changes

- Calculate one-day 95% historical Value at Risk and Conditional Value at Risk as positive loss magnitudes from effective daily returns, with an explicitly locked quantile/interpolation and tail-membership rule.
- Calculate bias-corrected Fisher-Pearson sample Skewness and bias-corrected Fisher excess Kurtosis, with the normal-distribution kurtosis baseline clearly labeled as zero.
- Expose observation count, tail observation count, six-decimal results, and `insufficient_evidence`/null behavior for small, constant, or otherwise undefined samples.
- Calculate and persist the four metrics for the strategy and each fixed benchmark on newly calculated normal and selected Walk-forward OOS backtests, leave legacy rows null without backfill, and retain the metric-family version used.
- Expose the values through reports, typed HTTP responses, Backtest Detail, and per-window/aggregate Walk-forward evidence without thresholds, scores, forecasts, or pass/fail conclusions; describe Walk-forward aggregates as statistics across independent window estimates rather than a VaR/CVaR calculation on a combined return distribution.

## Capabilities

### New Capabilities

- `tail-distribution-risk-metrics`: Defines historical one-day VaR/CVaR and bias-corrected return-shape statistics, including sample evidence, precision, sign, and undefined-boundary semantics.

### Modified Capabilities

- `backtest-benchmark-comparison`: Adds the same absolute distribution-risk metrics to each fixed benchmark curve.
- `backtest-execution`: Calculates and versions strategy and benchmark distribution metrics inside the existing caller-owned atomic boundary.
- `backtest-run-model`: Persists nullable distribution-risk fields and evidence counts while preserving legacy history without recalculation.
- `walk-forward-runner`: Retains the new values per selected OOS window and aggregates them with metric-local evidence counts rather than a verdict.
- `walk-forward-evaluation-history`: Versions, persists, validates, and queries the expanded tail-risk evidence document.
- `http-api-service`: Exposes new persisted values and expanded Walk-forward evidence through typed read-only responses.
- `web-frontend-app`: Presents explicitly historical one-day loss and distribution-shape metrics with counts, semantics, null states, and responsive accessibility.

## Impact

- `add-benchmark-regime-performance-metrics` is a semantic implementation prerequisite: this Change advances its `wf_evidence_v2` document to `wf_evidence_v3` rather than creating a competing v2 shape.
- Core metric types/functions, benchmark calculation, backtest execution, Walk-forward evidence/reporting, and deterministic numerical/boundary tests under `packages/core`.
- Nullable SQLAlchemy fields and one Alembic revision validated against test-owned file-backed SQLite databases only.
- Backtest/Walk-forward report serialization, FastAPI schemas/routes/OpenAPI tests, and Backtest/Walk-forward detail UI and tests.
- Existing NumPy may be reused for independently specified numerical primitives; no new risk library, parametric/Cornish-Fisher VaR, multi-day scaling, stress model, regulatory-capital claim, historical backfill, threshold verdict, or write to `vela.db`.

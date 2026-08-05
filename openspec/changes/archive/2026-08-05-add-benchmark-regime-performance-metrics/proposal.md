## Why

Vela can compare strategy and benchmark returns through differences, Tracking Error, and Information Ratio, but it cannot distinguish market exposure from benchmark-adjusted excess performance or show how the strategy participates in benchmark up and down regimes. The existing strictly aligned strategy and fixed-benchmark daily curves now provide the auditable inputs needed to add those diagnostics without inventing another data source.

## What Changes

- Calculate CAPM-style annualized Alpha, Beta, R-squared, and observation count against the existing `csi_300_buy_hold` ETF proxy only, with an explicit proxy-qualified interpretation rather than a claim about an official total-return index.
- Calculate monthly geometric-mean Up Capture and Down Capture plus selected-month counts separately against both fixed benchmarks after compounding strictly aligned daily observations into calendar-month returns and classifying months by the named benchmark's positive or negative monthly return.
- Define risk-free-rate, CAPM 252-session annualization, monthly capture aggregation, compounding, precision, insufficient-observation, zero-variance, zero-denominator, partial-edge-month, and exact-date-alignment semantics.
- Persist the new scalar comparison fields for newly calculated normal and selected Walk-forward OOS backtests, leave legacy rows null without backfill, and retain the metric-family version used by each new run.
- Expose the metrics through reports, typed HTTP responses, Backtest Detail, and per-window/aggregate Walk-forward evidence with metric-local counts and `insufficient_evidence`, without creating a strategy score or pass/fail decision.

## Capabilities

### New Capabilities

- `benchmark-regime-performance-metrics`: Defines the shared daily CAPM proxy-regression and monthly geometric up/down capture calculation contracts, evidence fields, precision, and invalid-boundary behavior.

### Modified Capabilities

- `backtest-benchmark-comparison`: Adds proxy-qualified CAPM metrics for the CSI 300 benchmark and monthly capture metrics for both fixed benchmark comparisons, including `equal_weight_monthly` without describing it as a market factor.
- `backtest-execution`: Calculates and versions the new benchmark-relative metrics inside the existing caller-owned atomic execution boundary.
- `backtest-run-model`: Persists nullable comparison fields and preserves legacy history without recalculation.
- `walk-forward-runner`: Retains the new values per selected OOS window and aggregates them as evidence without a verdict.
- `walk-forward-evaluation-history`: Versions, persists, validates, and queries the expanded benchmark-regime evidence document.
- `http-api-service`: Exposes the new persisted values and expanded Walk-forward evidence through typed read-only responses.
- `web-frontend-app`: Presents proxy-qualified CAPM and named-benchmark monthly capture evidence with explicit units, selected-month counts, null states, and responsive accessibility.

## Impact

- Core metric types/functions, benchmark result calculation, backtest execution, Walk-forward evidence and report code, and focused deterministic tests under `packages/core`.
- Nullable SQLAlchemy fields and one Alembic revision exercised only against test-owned file-backed SQLite databases during validation.
- Backtest and Walk-forward report serialization, FastAPI schemas/routes/OpenAPI tests, and Backtest/Walk-forward detail UI and tests.
- No new market-data provider, benchmark identity, configurable benchmark, external dependency, historical backfill, automatic threshold, or write to `vela.db`.
- `add-tail-distribution-risk-metrics` remains downstream because it advances the `wf_evidence_v2` document introduced here to `wf_evidence_v3`; it must not be applied before this Change is complete and verified.

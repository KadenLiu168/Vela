## Why

Vela's summary metrics and Walk-forward aggregates can hide a regime in which performance deteriorates inside one backtest or OOS window, while a single total return cannot reveal calendar consistency or seasonality. Persisted strategy and benchmark curves already contain the dated net-value evidence needed to derive rolling and calendar-period diagnostics without duplicating stored data; requested bounds separately describe whether the run scope covers a complete natural period.

## What Changes

- Derive fixed 63-effective-session trailing total return, annualized Volatility, and Sharpe series for a strategy and each fixed benchmark from their persisted daily curves, primarily for one-year OOS inspection and short-horizon regime diagnostics rather than as a universally optimal multi-year horizon.
- Derive compounded monthly and yearly returns for the strategy and both fixed benchmarks, preserving natural calendar buckets and identifying periods whose requested run scope does not cover the complete natural period.
- Require complete rolling windows, preserve the current population-variance, `risk_free_rate / 252`, and six-decimal conventions, and return no expanding-window approximations.
- Compute these read-only series in typed backend code for Backtest Detail responses and display them as accessible rolling charts and calendar return tables/heatmaps without browser-side financial arithmetic.
- Limit the capability to a normal backtest or one independently persisted OOS backtest; do not calculate rolling risk metrics or calendar buckets across stitched Walk-forward window-reset seams.

## Capabilities

### New Capabilities

- `backtest-return-stability-series`: Defines fixed-window rolling performance and calendar-period return derivation from one authoritative strategy or benchmark equity curve.

### Modified Capabilities

- `backtest-benchmark-comparison`: Requires both fixed benchmark curves to expose stability series using the same source dates and calculation conventions as the strategy.
- `http-api-service`: Extends Backtest Detail with typed derived rolling and calendar-period series while leaving list and run-creation payloads unchanged.
- `web-frontend-app`: Adds accessible rolling diagnostics and monthly/yearly return presentation to Backtest Detail, including OOS backtests opened through their existing links.

## Impact

- Pure core derivation types/functions and deterministic tests under `packages/core`, plus Backtest Detail query/serialization work.
- FastAPI detail schemas/OpenAPI tests and Backtest Detail React types, visualizations, responsive/accessibility tests, and deterministic browser coverage.
- The active `add-stitched-oos-equity-curve` Change is primarily a logical and integration-order prerequisite: this Change must rebaseline against its final stitched-reset contract so that no stability metric crosses a window seam. The primary endpoints and pages are distinct, although the Changes share API schema/client aggregation files and may touch Walk-forward exclusion regressions; this Change does not modify or derive metrics from the stitched result.
- No migration, persisted-field addition, backfill, CLI execution change, configurable window, new endpoint, external dependency, or write to `vela.db`.

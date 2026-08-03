## Context

`run_backtest` currently persists only strategy metrics and one strategy equity curve. Walk-forward runs an equal-weight configuration as an optional baseline, which inherits the base configuration's rebalance frequency. The requested comparison needs two fixed, reproducible references in normal backtests and in every OOS window without creating benchmark strategy signals or unrelated backtest runs.

## Goals / Non-Goals

**Goals:**

- Calculate, persist, and expose a same-universe monthly equal-weight benchmark and an `SSE:510300` CSI 300 ETF buy-and-hold benchmark.
- Use the same official-session axis, forward-adjusted price ratios, metric functions, cost rate, and missing-price fail-fast policy as the strategy.
- Preserve each benchmark's daily net-value series for detail review and produce total-return and CAGR differences.
- Replace the walk-forward configurable baseline with these two fixed OOS comparisons.

**Non-Goals:**

- No new market-index data source, benchmark configuration UI, dashboard/list expansion, or default-database validation.
- No Tracking Error, Information Ratio, Alpha, Beta, Sortino, Calmar, rolling statistics, or benchmark optimization.

## Decisions

### Dedicated benchmark calculator and persisted child records

Create a core benchmark calculator that consumes the ordered `TradingCalendar` dates and validated price rows, returns net-value points, and calls the existing metric functions. Persist a `BacktestBenchmark` child for each fixed key plus ordered `BacktestBenchmarkEquityCurve` rows. This keeps benchmark state tied to one strategy run and avoids generating extra signals through `run_backtest`.

Alternative considered: invoke `run_backtest` with an equal-weight configuration. Rejected because it writes independent signals/runs and preserves the wrong configurable cadence. Alternative considered: compute only in the API/UI. Rejected because results would not be reproducible or available to CLI and Walk-forward.

### Fixed definitions and execution timing

`equal_weight_monthly` allocates equally across the dated active universe on the first requested official session without an entry cost. It marks to market daily and, after the market move on each subsequent last official session of a calendar month, trades to equal weights using the configured transaction-cost rate. `csi_300_buy_hold` resolves active `SSE:510300`, allocates on the first requested official session without entry cost, and only marks to market thereafter. The calculation uses the existing forward-adjusted price ratio convention.

The first-session no-cost rule deliberately matches current strategy equity initialization. Charging an entry cost only to benchmarks would make the comparison asymmetric; changing the existing strategy entry convention is outside this change.

### Complete common input axis

The runner verifies the active, unique `SSE:510300` identity and its price on every requested official session before signal generation or result persistence. The equal-weight benchmark uses the same dated active universe already validated for the strategy. No benchmark is shortened, forward-filled, or made nullable when its required observation is absent.

### API and presentation shape

The run and detail responses add an ordered `benchmarks` collection. Each entry has a stable key, display name, five strategy-equivalent metric fields, and detail curve points; the response also contains ordered comparisons keyed by benchmark with total-return and CAGR differences. The detail page renders all three series together and benchmark metric/comparison cards. Dashboard and list response shapes remain unchanged.

### OOS-only Walk-forward comparisons

`run_backtest` accepts an internal flag to skip benchmark work for IS parameter trials. Each selected OOS run calculates and persists benchmarks, and the report copies their metrics/differences into each window result. The `baseline` configuration model, YAML setting, and old baseline fields are removed because the fixed equal-weight monthly benchmark replaces it and CSI 300 is always present.

## Risks / Trade-offs

- [Future pools may omit `SSE:510300`] → fail before any artifact is persisted and name the missing active identity.
- [Extra rows increase detail payload size] → only detail/run endpoints expose curves; list/dashboard stay compact and every curve is keyed/indexed by parent.
- [Historical runs lack benchmark rows] → preserve them unchanged; detail responses return an empty benchmark collection for pre-migration runs rather than fabricating results.
- [Benchmark date semantics diverge from strategy] → use `TradingCalendar` as the sole axis and fixed numeric tests for first entry, month-end rebalance, cost, and missing dates.

## Migration Plan

1. Add the two benchmark tables and ORM relationships in a new Alembic migration; no backfill runs.
2. Deploy code that writes benchmark children atomically with newly produced runs and reads empty collections from legacy runs.
3. Roll back code before schema only if necessary; downgrade drops only the new benchmark tables, so no unrelated historical strategy rows are changed.

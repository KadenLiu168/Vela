## Why

Historical signal generation repeatedly scans and copies the full multi-ETF price panel for every
rebalance date, then dual momentum filters the same per-ETF prefix again for trend and momentum
calculation. Runtime therefore grows poorly with backtest length even though every strategy already
declares the exact history it needs through `lookback_days()`.

## What Changes

- Resolve the bound strategy and its non-negative lookback once for a historical generation run.
- Index each ascending ETF price series by trade date and use bounded binary-search slices for each
  rebalance date.
- Supply at most the strategy-required prior observations plus the signal-date observation, while
  preserving inception-date eligibility and the no-future-data boundary.
- Reuse each ETF's per-date bounded series inside dual-momentum trend and momentum evaluation instead
  of filtering it repeatedly.
- Add result-equivalence, edge-case, and long-history performance regression coverage.
- Preserve public Python APIs, generated positions/results, persistence callbacks, backtest data
  snapshots, database behavior, and strategy-agnostic dispatch.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-signal-generation`: Historical generation will derive a bounded per-rebalance price
  window from the selected strategy's declared lookback without changing signal semantics.

## Impact

- Affected code: `strategy_signal_generation.py`, the dual-momentum strategy implementation, and
  focused core tests/benchmarks.
- Affected contracts: historical generation input preparation and its performance characteristics.
- Unchanged: REST/CLI/Web payloads, database schema and rows, checksum protocol, transaction
  boundaries, strategy registry API, and generated financial results.
- Dependencies: no new runtime dependency.

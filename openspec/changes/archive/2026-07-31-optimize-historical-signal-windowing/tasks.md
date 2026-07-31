## 1. Lock Historical-Generation Contracts

- [x] 1.1 Add focused failing tests that compare weekly and monthly historical results, positions,
  ranks, scores, weights, expected failures, and persistence callback ids against controlled
  pre-optimization expectations.
- [x] 1.2 Add failing coverage for strategy resolution once per historical call, zero and positive
  lookbacks, no-future-data slicing, ETF inception boundaries, empty dates, and clearly rejected
  unsorted price sequences.
- [x] 1.3 Add a deterministic long-history scale regression that bounds cumulative strategy input
  rows by eligible rebalances, ETFs, and `lookback_days() + 1` without relying only on elapsed time.
- [x] 1.4 Add focused dual-momentum coverage proving one prepared per-ETF series is reused for trend
  and momentum while existing financial outputs remain exact.

## 2. Implement Bounded Window Preparation

- [x] 2.1 Refactor single-date and historical generation through one internal helper that preserves
  shared success, expected-failure, result, and callback semantics while resolving the bound
  strategy only once for a historical call.
- [x] 2.2 Build one ETF lookup and aligned ascending trade-date indexes, validate the ordering
  precondition, and use `bisect_right` to create inception-safe windows bounded to the declared
  lookback plus signal observation.
- [x] 2.3 Remove the nested active-ETF lookup and repeated full-prefix list filtering from historical
  generation without adding concrete-strategy branches or database access.
- [x] 2.4 Prepare each dual-momentum ETF series once per signal date and reuse it for trend and
  momentum evaluation without changing forward-adjusted calculations or fallback behavior.

## 3. Verify Correctness and Performance

- [x] 3.1 Run the focused strategy registry, signal-generation, and backtest-runner tests and confirm
  controlled results, callbacks, inception behavior, snapshot coverage, and rerun isolation remain
  unchanged.
- [x] 3.2 Record a repeatable synthetic long-history before/after benchmark as supplementary evidence
  and confirm the deterministic bounded-row regression passes.
- [x] 3.3 Run the complete Python CI-equivalent gate: `uv sync --group dev`,
  `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`,
  `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 3.4 Run target and global strict OpenSpec validation, `openspec doctor`, and `git diff --check`;
  review the final diff for unrelated changes and confirm no persistent database operation occurred.

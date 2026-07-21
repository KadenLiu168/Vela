## Context

`MarketPrice.strategy_price` is a property on the ORM model that computes `close_price × factor_hfq` at access time. It is consumed by signal/trend calculations, standalone returns/moving-average calculations, the equity curve, and the ETF trend endpoint. Backtest execution itself continues to use unadjusted `close_price`. The model lives in `models/market_price.py:48-50`.

`factor_hfq` is stored via an upsert in `market_price_upsert.py:41-55` that intentionally excludes the factor from the `ON CONFLICT DO UPDATE SET` clause. The rationale was "append-only snapshot immunity" — but backward-adjustment factors are mathematically not append-only; they are recomputed by data providers relative to the latest date whenever a corporate action occurs.

`forward_adjusted_prices()` in `adjusted_price_projection.py:29-59` is a pure function that normalizes the factor-multiplied series against a rebalance-date anchor (`qfq(D) = close(D) × factor(D) / factor(T)`). It has passing tests in `test_adjusted_price_projection.py` but zero production callers.

The fix has two layers: correct the data (`factor_hfq` in upsert) and correct the consumption (normalize through `forward_adjusted_prices` before any ratio calculation).

## Goals / Non-Goals

**Goals:**

- Eliminate cross-batch factor anchor inconsistency in stored data by including `factor_hfq` in the upsert conflict SET
- Migrate all consumers from direct `strategy_price` access to `forward_adjusted_prices()` normalization
- Remove `MarketPrice.strategy_price` property to prevent future misuse
- Preserve existing consumer API contracts — `MomentumScore`, `TrendFilterResult`, `StrategyEquityCurvePoint` etc. remain unchanged

**Non-Goals:**

- Changing the `DailyPrice.factor` contract or provider implementations
- Modifying how `forward_adjusted_prices` itself works (it is correct as-is)
- Adding caching or persistence for forward-adjusted prices
- Changing the `MarketPrice` table schema (factor_hfq column stays, only the upsert behavior changes)

## Decisions

### Decision 1: Add `factor_hfq` to upsert conflict SET (not separate force-update path)

The `_collect_incremental_prices` function already detects corporate actions by comparing stored vs upstream factors at the boundary date. When a mismatch is found, it triggers a full refetch. But the subsequent `upsert_market_prices` call rejects the factor update for existing rows.

**Alternative considered**: Conditionally include `factor_hfq` only when a corporate action is detected. This would require threading a flag through the call chain (`_collect_incremental_prices` → `upsert_market_prices`). Adds complexity, couples the fetcher to the upsert, and introduces a code path that tests would need to cover.

**Why always include**: During normal incremental fetches, re-fetched rows have the same factor as stored rows — the update is a no-op. During corporate action refetches, the factor has legitimately changed and must be updated. Always including it is correct in both cases, simpler, and eliminates the coupling.

### Decision 2: Each consumer owns its projection anchor; the equity curve projects per interval

**Alternative considered**: Modify `load_price_panel` to return pre-normalized `ForwardAdjustedPrice` lists. This would be a single integration point but requires passing `rebalance_date` into the panel loader, which doesn't currently have a concept of anchor dates. Panel loading is general-purpose; normalization is consumer-specific.

**Why per-consumer**: The rebalance date varies per consumer call (momentum scoring for date T, trend filtering for the same date, etc.). Each consumer already knows its anchor date. Adding normalization at the top of each pure-function computation (`_momentum_score_from_prices`, `_trend_filter_from_prices`, `_moving_average_from_prices`, etc.) keeps concerns separated and anchors explicit.

For the ETF trend endpoint, the resolved latest date of the selected range is the anchor. This intentionally changes only the numeric scale of the existing `price` field (not URL, shape, ordering, or range semantics); its final point becomes the observable unadjusted close, which is the least surprising chart readout.

`strategy_equity_curve` is the exception that makes the anchor rule important: it calculates a return for every adjacent pair of trading dates, so each pair must be projected with the *current* interval date as its anchor. `_load_prices_by_key` therefore remains a raw `MarketPrice` cache. `_calculate_daily_return` obtains its previous/current rows and calls `forward_adjusted_prices([previous, current], rebalance_date=current_date)` only after both rows exist. A single `(etf_id, trade_date) -> Decimal` cache of normalized values is invalid because the same date can require different anchors in adjacent intervals.

### Decision 3: Remove `strategy_price` property, not deprecate

**Alternative considered**: Keep as deprecated with a warning. But Python property access has no mechanism for warnings without triggering at import time or adding runtime overhead. A removed property causes `AttributeError` at the call site — loud, immediate, impossible to miss. A deprecated warning could be silenced accidentally in logs.

**Why remove**: Safety through loud failure. Every consumer must be explicitly migrated; there's no risk of silent drift back to the old pattern.

### Decision 4: Normalize at the narrowest computation boundary

The codebase has two patterns: pure-function computation (e.g., `_momentum_score_from_prices`) and session/query functions. Compatibility wrappers such as `calculate_momentum_score` and `apply_trend_filter` only load data and delegate, so they do not need normalization logic. Other session/query paths — `calculate_market_price_returns`, `get_etf_price_trend`, and the equity-curve loader/calculator — currently consume `strategy_price` directly and must be migrated at their own computation boundary.

**Why this boundary**: Put `forward_adjusted_prices` immediately before price arithmetic, while leaving query-only wrappers unchanged. This keeps anchors explicit, avoids pushing consumer-specific semantics into `load_price_panel`, and limits edits to functions that actually transform prices.

### Decision 5: Correct existing active data with a successful full fetch, not a schema migration

Changing the conflict update set repairs factors only when rows are subsequently upserted. An already inconsistent local database is not guaranteed to encounter another factor mismatch on its next incremental fetch, so incremental fetch alone is not a repair procedure.

**Decision**: after deploying this change, run the existing full fetch command, without `--incremental`, against a recoverable copy of every retained local database. The full fetch maps provider rows and invokes `upsert_market_prices`; the corrected conflict set rewrites every fetched existing row within the caller-managed transaction. No table shape changes and no new migration are required.

The existing fetcher handles provider failures per ETF: it can return `partial` and the CLI-managed session still commits successful symbols. Therefore repair is complete only when the command returns `success` with no failed symbols; a partial run must be retried after the provider failure is resolved. The full-fetch universe is `_active_etfs`, so inactive ETF history is deliberately outside automatic repair. If an inactive ETF must become strategy-usable again, it must first re-enter the active pool through the normal configuration/sync workflow and then receive a successful full fetch.

### Decision 6: Do not rewrite persisted signals or backtest runs

`StrategySignal` and `BacktestRun` rows store outputs calculated under the data snapshot available at their creation time. The full fetch repairs raw market data but does not mutate those historical outputs.

**Why**: Automatically regenerating them would add unclear selection rules, rewrite provenance, and turn a focused market-data correction into a broad historical-data migration. Operators can explicitly rerun the signals and backtests they want to compare after the full fetch.

## Risks / Trade-offs

- **Risk**: A consumer that uses `strategy_price` but doesn't appear in the grep results (e.g., dynamic attribute access or future code).  
  → **Mitigation**: Running `pytest` after removing the property will fail runtime accesses, mypy will flag removed attributes on typed code paths, and the repository search must have no production usages. The one negative model-contract test may intentionally access the missing attribute to assert `AttributeError`.

- **Risk**: `forward_adjusted_prices` raises `ValueError` when `rebalance_date` is not in the price series. Consumer callers that previously handled missing-as-of-date data by returning early (e.g., `prices[-1].trade_date != as_of_date`) must now check BEFORE calling normalization.  
  → **Mitigation**: Existing early-return guards in the targeted computation paths check this condition. Normalization is placed after those guards; `get_etf_price_trend` anchors to the same `end_date` used to load its non-empty panel.

- **Risk**: The equity-curve loader currently caches one `Decimal` per `(etf_id, trade_date)`. Replacing those values with a single projected price would silently select the wrong anchor for one of the adjacent intervals.  
  → **Mitigation**: Keep raw `MarketPrice` rows in that cache and project exactly the pair used for each interval inside `_calculate_daily_return`.

- **Trade-off**: `forward_adjusted_prices` recomputes normalization on every call. This is intentional — it's a pure function, no cache invalidation problem, and price series in this codebase are small (typically < 252 trading days per consumer call). Computational cost is negligible.

- **Trade-off**: The release requires provider availability for one full refetch to repair prior local data. This is deliberately operational rather than automatic: silently deleting/reloading local research data on application startup would be a larger and less controllable behavior change.

- **Trade-off**: A partial full fetch commits repairs for successful active ETFs and leaves failed or inactive ETFs untouched. This matches existing fetch semantics; operational completion therefore requires a successful retry and an explicit record that inactive history was not repaired.

- **Trade-off**: A provider can return an unexpectedly incomplete history without raising a per-symbol error. The Change does not add completeness reconciliation or delete stale dates; the operational full-fetch repair assumes the provider returns its intended full history, while existing gap warnings remain the available diagnostic.

- **Trade-off**: Stored signal and backtest records can continue to display values calculated before the repair until explicitly rerun. They remain valid provenance of their original input snapshot; the system does not relabel or overwrite them.

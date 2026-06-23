## Context

Vela already generates and persists one strategy signal for a requested `signal_date`. That path calculates momentum scores, applies the trend filter, selects target positions or the defensive fallback, and writes `StrategySignalPosition` rows. COP-55 added deterministic weekly rebalance date generation from historical trading dates.

COP-56 connects those two existing pieces for backtesting: given historical trading dates, generate signals only on historical rebalance dates while keeping each signal calculation scoped to that date.

## Goals / Non-Goals

**Goals:**
- Reuse existing single-date strategy signal generation for each historical rebalance date.
- Use COP-55 weekly rebalance dates derived from caller-provided historical trading dates.
- Return generated signal results in chronological order.
- Persist results through the existing strategy signal tables so portfolio holding calculation can consume target weights later.
- Keep no-future-data behavior by passing each rebalance date as the `signal_date`/`as_of_date` boundary.

**Non-Goals:**
- Implement portfolio holdings, equity curves, or a full backtest runner.
- Add a CLI command or API endpoint.
- Change strategy rules, signal persistence schema, or rebalance-date rules.
- Infer missing trading dates from calendars or external services.

## Decisions

1. Add a small helper in `strategy_signal_generation.py`.

   Rationale: the existing single-date generation function already owns strategy signal orchestration and persistence. Keeping historical orchestration beside it avoids a new module for one narrow workflow.

   Alternative considered: create a `backtest_signal_generation.py` module. That would be reasonable once a broader backtest runner exists, but it is premature for only looping over rebalance dates.

2. Accept historical trading dates as input.

   Rationale: COP-55's rebalance generator is intentionally based on available input dates. Reusing that contract keeps holiday and missing-data behavior explicit and avoids querying unrelated ETF histories.

   Alternative considered: query all distinct `MarketPrice.trade_date` values inside the helper. That hides the date universe choice and makes later backtests less explicit.

3. Return `list[GenerateStrategySignalResult]`.

   Rationale: this preserves the existing result shape and gives later portfolio holding calculation direct access to signal ids, dates, statuses, and generated positions.

   Alternative considered: introduce a new batch result dataclass. The current need does not require aggregate metadata beyond the ordered list.

## Risks / Trade-offs

- Caller provides an incomplete trading-date sequence -> Generated rebalance dates reflect only the provided sequence, matching the existing COP-55 contract.
- Repeated historical generation creates additional signal runs for the same date -> Existing signal persistence already preserves reruns instead of replacing prior runs.
- A failed signal on one historical date could coexist with successful later dates -> The helper should keep returning each per-date result instead of aborting the batch, matching single-date persistence semantics.

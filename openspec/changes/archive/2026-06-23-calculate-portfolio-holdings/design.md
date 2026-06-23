## Context

Strategy signal generation already persists successful rebalance signals and their target positions with `target_weight`. Backtesting now needs a daily portfolio holding series that makes the rebalance boundary explicit without introducing equity-curve or trading-cost logic in this change.

## Goals / Non-Goals

**Goals:**
- Provide a core helper that converts successful persisted strategy signal positions into daily target holding snapshots.
- Support both a single date and an interval represented by caller-provided trading dates.
- Make holdings before the first applicable signal empty and carry the latest signal positions forward after each rebalance date.
- Keep the output deterministic, typed, and easy for later backtest steps to consume.

**Non-Goals:**
- Do not create or modify database tables.
- Do not calculate market value, net value, returns, turnover, or transaction costs.
- Do not add a CLI or API command.
- Do not generate strategy signals; callers remain responsible for signal generation before holding calculation.

## Decisions

- Use persisted successful `StrategySignal` rows as rebalance events.
  - Rationale: COP-57 asks for holdings based on signals, and existing signal persistence already records target ETF weights.
  - Alternative considered: accept generated signal result objects directly. That would be useful for in-memory workflows but would not cover historical runs already persisted for backtesting.

- Select the newest successful signal for each `signal_date` and `config_version`.
  - Rationale: the existing persistence contract preserves reruns; holding calculation should use the latest successful run for a date.
  - Alternative considered: use all successful runs and require the caller to choose. That exposes unnecessary persistence details to portfolio calculation.

- Return target-weight holdings, not share quantities.
  - Rationale: COP-57 acceptance focuses on holdings and target weights; share sizing requires prices, cash, slippage, and transaction-cost decisions that belong to later backtest execution.
  - Alternative considered: compute shares. That would prematurely couple this capability to valuation logic.

- Treat caller-provided trading dates as the output calendar.
  - Rationale: market-data calendar ownership already sits outside this helper, and tests can verify date-range behavior without adding calendar rules here.
  - Alternative considered: query all market dates internally. That would mix portfolio state calculation with market-data availability concerns.

## Risks / Trade-offs

- Missing pre-generated signals for a range -> holdings remain empty or unchanged. Mitigation: document that callers must generate signals before requesting holdings.
- Duplicate successful signal reruns on one date -> latest generated signal wins. Mitigation: order by `generated_at` and id for deterministic selection.
- Output target weights only -> later backtest steps still need valuation and execution logic. Mitigation: keep this change scoped to COP-57 and leave equity-curve work to a later COP.

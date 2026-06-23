## Context

COP-58 added a deterministic strategy equity curve using carried portfolio holding snapshots and market prices. That calculation currently produces a frictionless daily return. COP-59 adds the next backtest concern: transaction costs configured by the strategy.

The existing strategy configuration already exposes `costs.transaction_cost_bps`, and COP-57 holdings expose target weights per date. There is no executed-order model or cash ledger in Phase 1, so the calculation needs to stay target-weight based.

## Goals / Non-Goals

**Goals:**
- Deduct transaction costs from daily equity curve returns when target holdings change.
- Source the transaction cost rate from `StrategyConfig.costs.transaction_cost_bps`.
- Keep the calculation deterministic and covered by focused unit tests.

**Non-Goals:**
- Do not add slippage, bid/ask spread, tax, cash yield, or broker execution logic.
- Do not persist cost details to database tables.
- Do not create a CLI/API entrypoint for running backtests.

## Decisions

### Use target-weight turnover

Calculate turnover as the sum of absolute target weight changes between the previous and current holding snapshots, keyed by ETF id. This covers entering, exiting, and rebalancing holdings with the data model already available.

Alternative considered: calculate transaction amount from shares and prices. That would require a share-sizing and cash model that does not exist yet and would exceed COP-59.

### Deduct costs from daily return

For each non-initial point, calculate:

`daily_return = weighted_price_return - turnover * transaction_cost_bps / 10000`

Then apply the existing net value update rule. This keeps transaction costs visible through daily return and net value without changing the returned dataclass.

Alternative considered: add a separate cost field to `StrategyEquityCurvePoint`. That could be useful later, but COP-59 only requires cost deduction and would broaden the public output contract now.

### Pass strategy configuration into equity curve calculation

Use `StrategyConfig` as the cost source and use `strategy_config.version` when loading holdings. This directly satisfies the requirement that transaction cost parameters come from strategy configuration.

Alternative considered: load `config/strategy_v1.yaml` inside `calculate_strategy_equity_curve`. That would hide I/O in a calculation helper and make tests less explicit.

## Risks / Trade-offs

- Target weights approximate executed turnover rather than realized order amounts -> acceptable for Phase 1 because holdings are represented as target weights, not shares.
- Rebalance-day cost is based on the new target snapshot versus the previous target snapshot -> tests document this rule so a future execution model can intentionally replace it.
- Zero-cost configurations should preserve frictionless behavior -> covered with a unit test.

## Context

`calculate_strategy_equity_curve` already calculates daily net value points from portfolio holding snapshots and `MarketPrice.strategy_price`. Existing tests cover several individual behaviors, but COP-72 asks for explicit coverage that ties together base holding returns, the initial net value, daily net values, and rebalance impact.

## Goals / Non-Goals

**Goals:**
- Add focused regression tests for strategy equity curve net value calculation.
- Use deterministic in-memory SQLite data with persisted signals, positions, and market prices.
- Assert the complete daily curve values needed by COP-72 acceptance criteria.
- Keep production code unchanged unless the tests expose an incorrect calculation.

**Non-Goals:**
- Do not change the equity curve API shape.
- Do not change transaction cost, annualized return, volatility, drawdown, Sharpe ratio, persistence, runner, or CLI behavior.
- Do not add dependencies or broaden test infrastructure.

## Decisions

1. Add a single end-to-end equity curve test for the acceptance path.

   Rationale: one multi-day scenario can verify initial value, daily values, weighted held-position returns, and a rebalance effect together without duplicating setup across several narrow tests.

   Alternative considered: separate one-assertion tests for each acceptance criterion. Existing tests already cover several pieces separately; another combined acceptance test better protects the integrated behavior COP-72 names.

2. Use simple exact price ratios and `Decimal` expected values.

   Rationale: exact ratios make the expected net values reviewable and avoid float-derived expected values.

   Alternative considered: calculate expected values inside the test from the same formula. That would be less useful because it could mirror the implementation instead of documenting expected behavior.

## Risks / Trade-offs

- Combined tests can be harder to diagnose than isolated tests -> keep the scenario small, with three dates and one explicit rebalance.
- Existing tests already cover related behavior -> add one acceptance-focused test rather than broad refactoring or duplicate helper churn.

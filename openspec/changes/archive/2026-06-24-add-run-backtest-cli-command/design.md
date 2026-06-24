## Context

Previous changes added the calculation and persistence pieces needed for backtesting: historical signal generation, portfolio holdings, equity curve calculation, annualized return, maximum drawdown, volatility, Sharpe ratio, and `persist_backtest_result`. COP-65 connects those pieces into an executable workflow and exposes it through the CLI.

The user selected these Explore decisions:
- `run-backtest` SHALL generate historical strategy signals before calculating the backtest.
- Persisted curve rows SHALL use normalized snapshots rather than real account accounting.
- Trading dates SHALL come from distinct local `MarketPrice.trade_date` values in the requested date range.

## Goals / Non-Goals

**Goals:**

- Add `run_backtest(...)` in the core package.
- Add `vela run-backtest --start-date YYYY-MM-DD --end-date YYYY-MM-DD`.
- Persist one new backtest result per CLI run.
- Output core metrics and the persisted run id.

**Non-Goals:**

- Do not implement real cash/share accounting or initial capital.
- Do not fetch missing market data.
- Do not update existing backtest runs.
- Do not add web/API surfaces.

## Decisions

1. Keep the orchestration in `vela_core.backtest_runner`.

   Rationale: CLI commands in this project parse arguments and print summaries while core business logic lives in `vela_core`.

2. Generate historical signals inside the runner.

   Rationale: `run-backtest` should run a complete backtest for the requested config/date range. Requiring a separate signal generation step would make the CLI workflow incomplete.

3. Use local `MarketPrice.trade_date` as the trading calendar.

   Rationale: Phase 1 already treats local market data as the source of truth. This avoids external calendars and keeps missing ETF prices subject to existing neutral contribution behavior.

4. Persist normalized equity curve snapshots.

   Rationale: The current calculation produces net value and target holdings, not cash/share accounting. Normalized snapshots preserve queryable curve and holdings information without inventing a trading ledger.

## Risks / Trade-offs

- Repeated runs create repeated historical signal rows -> This matches existing run-history behavior and avoids update semantics.
- Normalized `cash` and `market_value` are not real account balances -> Keep the fields explainable and defer real accounting to a dedicated future change.
- Empty date ranges cannot produce a meaningful backtest -> Fail before persisting and surface the error to the CLI.

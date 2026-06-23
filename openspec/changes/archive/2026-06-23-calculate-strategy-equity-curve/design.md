## Context

COP-57 introduced `calculate_portfolio_holdings`, which converts successful strategy signals into daily target holding snapshots. The backtest models already include `BacktestEquityCurve`, and market prices already expose `strategy_price` as adjusted close when available, otherwise close price.

COP-58 needs the calculation layer between those pieces: a deterministic net value curve that later backtest orchestration can persist or analyze.

## Goals / Non-Goals

**Goals:**
- Provide a core function that returns one equity curve point for each requested trading date.
- Use existing daily portfolio holding snapshots as the holding source.
- Use existing market price rows and `strategy_price` for daily ETF returns.
- Make initial and daily net value rules explicit and covered by tests.

**Non-Goals:**
- Persist equity curve rows to `BacktestEquityCurve`.
- Create or update `BacktestRun` rows.
- Add CLI/API entrypoints.
- Add transaction costs, slippage, dividends beyond adjusted close, cash yield, or performance metrics.

## Decisions

### Pure calculation before persistence

Add a pure core calculation service that returns dataclass value objects instead of ORM rows.

Alternative considered: write `BacktestEquityCurve` rows directly. That would couple calculation to run lifecycle and persistence before the backtest execution workflow exists.

### Initial net value and daily returns

The first requested trading date starts at `1.000000`. Each later point uses:

`net_value_today = net_value_yesterday * (1 + weighted_return_today)`

`weighted_return_today` is the sum of each current holding's target weight multiplied by that ETF's one-period price return from the previous requested trading date to the current requested trading date.

### Missing return inputs are neutral

If a held ETF is missing either the previous or current strategy price, that holding contributes `0` to the daily weighted return. This keeps the calculation deterministic for sparse Phase 1 data and avoids inventing failure semantics before the backtest runner exists.

## Risks / Trade-offs

- Sparse price data can understate returns when a held ETF is missing prices -> tests document neutral contribution so later backtest validation can decide whether to fail earlier.
- Target weights are treated as daily weights rather than share quantities -> acceptable for Phase 1 because COP-57 produces target allocation snapshots, not executed positions.
- No persistence in this change -> later COPs must explicitly map returned points into `BacktestEquityCurve` rows if storage is required.

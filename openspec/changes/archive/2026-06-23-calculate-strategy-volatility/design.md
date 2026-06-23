## Context

`strategy_equity_curve.py` already calculates daily strategy net value points, annualized return, and maximum drawdown. Each `StrategyEquityCurvePoint` includes a `daily_return`; the first point uses `0.000000` as an initialization placeholder rather than an observed strategy return.

COP-62 needs the same module to expose annualized volatility for later backtest run summaries.

## Goals / Non-Goals

**Goals:**
- Calculate annualized volatility from strategy equity curve daily returns.
- Document the calculation basis in tests and OpenSpec.
- Keep the API small and consistent with existing metric helpers.

**Non-Goals:**
- Persist volatility to `BacktestRun`.
- Add CLI or API behavior.
- Change equity curve, annualized return, or maximum drawdown behavior.
- Add configurable annualization factors.

## Decisions

1. Add `calculate_strategy_volatility(points)` to `strategy_equity_curve.py`.

   Rationale: Annualized return and maximum drawdown already live in this module and operate on `StrategyEquityCurvePoint` lists. Keeping volatility there avoids a new one-function module and keeps backtest metric helpers discoverable.

   Alternative considered: accept a raw `list[Decimal]` return series. That is smaller in isolation, but callers already have equity curve points, and using points makes it explicit that the first placeholder return is ignored.

2. Exclude the first equity curve point's `daily_return`.

   Rationale: `calculate_strategy_equity_curve` seeds the first point with `daily_return=0.000000` because no prior trading interval exists. Including that placeholder would understate volatility.

   Alternative considered: include all point returns. That would be simpler, but it would mix an initialization value with observed returns.

3. Use population standard deviation of effective daily returns and annualize with `sqrt(252)`.

   Rationale: Backtest volatility should describe the realized variability of the provided return sequence, and 252 trading days is the conventional daily-return annualization factor for ETF strategy metrics. Population standard deviation keeps the result deterministic for the exact observed backtest period without applying sample-size correction.

   Alternative considered: sample standard deviation with `n - 1`. That is also common for estimates, but this Phase 1 metric is a deterministic summary of the produced backtest path.

4. Return a dataclass with nullable `volatility`.

   Rationale: This matches the existing `StrategyAnnualizedReturn` shape for metrics that may be unavailable and gives later summary code a stable result type.

## Risks / Trade-offs

- Different analytics tools may default to sample standard deviation -> Tests and specs make Vela's population-standard-deviation basis explicit.
- `Decimal` does not provide square root ergonomics for every operation needed here -> Use float only for square root/annualization conversion, then quantize back to `Decimal("0.000001")`, matching the existing annualized return helper's pragmatic numeric approach.

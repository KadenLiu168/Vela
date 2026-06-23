## Context

`calculate_strategy_equity_curve` already produces ordered curve points with `trade_date`, `net_value`, and `daily_return`. COP-60 needs annualized return from that curve without introducing a full backtest reporting layer.

## Goals / Non-Goals

**Goals:**

- Provide a small backend API that calculates annualized return from curve points.
- Make the calculation basis explicit and testable.
- Keep precision consistent with existing six-decimal strategy equity outputs.

**Non-Goals:**

- Persist annualized return to `BacktestRun`.
- Add CLI or report output.
- Add other performance metrics such as max drawdown, volatility, or Sharpe ratio.

## Decisions

- Calculate from first and last curve points using calendar days:
  `ending_net_value / starting_net_value` raised to `365 / elapsed_calendar_days`, minus `1`.
  Calendar days make the annualization basis explicit from the curve dates and avoid assuming a fixed number of trading days for ETF markets.
- Return `None` when the curve has fewer than two points, the elapsed day span is not positive, or the starting net value is not positive. These cases do not have a meaningful annualized return.
- Return a small dataclass with `total_return` and `annualized_return` so callers can reuse both period and annualized performance without recalculating.
- Quantize outputs to six decimal places to match existing equity curve output.

## Risks / Trade-offs

- Calendar-day annualization can differ from trading-day annualization. The口径 is explicit in the spec and tests so downstream reports can label it correctly.
- Decimal exponentiation for fractional years converts through `float`. This is acceptable for a phase-1 six-decimal metric and avoids adding dependencies or complex numeric code.

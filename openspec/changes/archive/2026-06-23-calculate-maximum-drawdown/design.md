## Context

`strategy_equity_curve.py` already owns the in-memory strategy equity curve point model and return metric helpers. COP-61 adds another metric over the same point list: maximum drawdown.

## Goals / Non-Goals

**Goals:**

- Calculate maximum drawdown from `StrategyEquityCurvePoint` values without querying storage.
- Return the drawdown value and the peak/trough dates that define the interval.
- Keep numeric output quantized to six decimal places, matching existing curve and return metrics.

**Non-Goals:**

- Persist max drawdown to `BacktestRun`.
- Add CLI, API, or report output.
- Recalculate equity curve points or alter transaction cost behavior.

## Decisions

1. Return a frozen dataclass from a pure helper.

   Rationale: this matches `StrategyAnnualizedReturn`, keeps the function easy to test, and avoids coupling metric calculation to database state.

2. Express drawdown as `current_net_value / running_peak_net_value - 1`.

   Rationale: the existing `BacktestRun.max_drawdown` model tests use negative drawdown examples, and a negative decimal preserves direction without needing a separate sign convention.

3. Return `0.000000` with no interval for empty, flat, or all-rising curves.

   Rationale: no loss from a prior peak occurred, so there is no meaningful peak-to-trough interval to report.

## Risks / Trade-offs

- Same-date duplicate points could produce ambiguous intervals -> Use the input order as the curve order, matching existing metric helpers.
- Non-positive peak net values would make percentage drawdown invalid -> Ignore drawdown calculation until a positive running peak exists.

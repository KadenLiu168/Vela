## Context

`calculate_strategy_sharpe_ratio` currently takes two pre-computed metrics (`StrategyAnnualizedReturn` and `StrategyVolatility`) and a risk-free rate, then computes `(cagr - rf) / vol`. The problem is that CAGR uses 365 calendar days for annualization while Volatility uses √252 trading days — two different conventions mixed in one ratio.

The equity curve already exposes one six-decimal `daily_return` per requested trading interval. Its first point is an initialization placeholder with `daily_return=0.000000`, not an observed return. The volatility helper already treats `points[1:]` as the effective observations and uses population variance.

The fix decouples Sharpe from CAGR and annualized volatility, computing it from the same effective daily return observations. `calculate_strategy_sharpe_ratio` is exported from `vela_core`, so changing its parameters is a public Python API break even though repository search finds only one production call site.

## Goals / Non-Goals

**Goals:**
- Compute Sharpe ratio directly from daily excess returns, independent of CAGR annualization convention
- Use the same effective-return boundary and population-dispersion convention as strategy volatility
- Keep CAGR and Volatility functions unchanged — each retains its semantically correct convention
- Preserve the `StrategySharpeRatio` result type and all REST, CLI, Web, and database schemas
- Keep all existing non-Sharpe behavior unchanged

**Non-Goals:**
- Change CAGR or Volatility annualization formulas
- Add new performance metrics (Information Ratio, Sortino, etc.)
- Modify the backtest database schema or API response format
- Recalculate or backfill Sharpe values for previously persisted backtest runs
- Add metric-version metadata

## Decisions

### Decision 1: Compute Sharpe from daily returns, not derived annualized metrics

**Chosen**:

1. Read effective daily returns from `points[1:]`, excluding the initial placeholder.
2. Calculate `daily_excess_return = daily_return - risk_free_rate / 252`.
3. Calculate the population standard deviation of the effective daily excess returns.
4. Return `mean(daily_excess_returns) / population_stddev(daily_excess_returns) × √252`, quantized to six decimal places.

**Alternatives considered**:

| Option | Verdict | Reason |
|---|---|---|
| Change CAGR to use 252 trading days | Rejected | "Trading-year CAGR" is non-standard; mixes the meaning of CAGR |
| Change Volatility to use √365 | Rejected | Wrong — daily returns only exist on trading days, √365 inflates by ~20% |
| Reuse the quantized annualized volatility result | Rejected | Dividing by an already quantized intermediate changes the final ratio and leaves Sharpe coupled to another metric's representation |
| Compute Sharpe from effective daily excess returns × √252 | **Chosen** | Uses one internally consistent trading-day convention and the existing equity-curve observations |

Population standard deviation is intentional and matches `calculate_strategy_volatility`: the backtest return sequence is the full realized population being summarized, not a sample used to estimate another dataset.

### Decision 2: Change function signature

**Chosen**: `calculate_strategy_sharpe_ratio(points: list[StrategyEquityCurvePoint], *, risk_free_rate: Decimal) -> StrategySharpeRatio`

Previously: `(annualized_return: StrategyAnnualizedReturn, volatility: StrategyVolatility, *, risk_free_rate: Decimal)`

The function now receives the raw equity curve data and self-contains the computation. This is a BREAKING change to the public Python API, but:
- The function is a public `vela_core` export, so callers outside this repository must migrate
- No REST/CLI/Web response or persistence schema is affected
- Only one call site exists (`backtest_runner.py`)
- The function maintains the same return type (`StrategySharpeRatio`)

### Decision 3: Daily risk-free rate

**Chosen**: `risk_free_rate / 252` for daily risk-free rate used in excess return calculation.

This treats the configured annual rate as a nominal arithmetic rate spread over 252 trading sessions. An exact compounded conversion such as `(1 + risk_free_rate) ** (1 / 252) - 1` is not chosen because the existing configuration does not define the rate as an effective annual yield and the requested correction is to use one consistent 252-day arithmetic-return convention.

### Decision 4: Preserve historical persisted results

Existing `BacktestRun.sharpe_ratio` values remain unchanged. New backtests persist the corrected value in the same nullable `Numeric(18, 6)` column, and API/CLI/Web consumers continue reading the same field.

Backfilling would require defining which historical runs are eligible and performing a persistent data update. That is outside this calculation fix and must not be inferred during Apply.

## Risks / Trade-offs

- **Public Python signature change**: repository code has one production caller, but external `vela_core` consumers are not discoverable here. The breaking change is explicit and limited to one function.
- **Mixed historical semantics**: old and new `BacktestRun.sharpe_ratio` values share the same column without a metric-version marker. This is accepted because no backfill or schema change is authorized; comparisons across runs created before and after this change must account for it.
- **Arithmetic daily risk-free approximation**: `risk_free_rate / 252` is simple and consistent with the selected arithmetic-return convention, but differs slightly from compounded daily conversion.
- **Duplicated local variance calculation**: Sharpe repeats the small mean/variance calculation rather than reusing the quantized volatility output. Introducing a shared abstraction is unnecessary for this focused fix.

## Open Questions
<!-- None -->

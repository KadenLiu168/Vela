from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.errors import BacktestDataError
from vela_core.models import ETFInfo, MarketPrice
from vela_core.strategy_equity_curve import (
    StrategyAnnualizedReturn,
    StrategyEquityCurvePoint,
    StrategyMaximumDrawdown,
    StrategySharpeRatio,
    StrategyVolatility,
    calculate_strategy_annualized_return,
    calculate_strategy_maximum_drawdown,
    calculate_strategy_sharpe_ratio,
    calculate_strategy_volatility,
)

_SIX_PLACES = Decimal("0.000001")
_BASIS_POINTS = Decimal("10000")


@dataclass(frozen=True)
class BacktestBenchmarkResult:
    key: str
    name: str
    points: list[StrategyEquityCurvePoint]
    annualized_return: StrategyAnnualizedReturn
    maximum_drawdown: StrategyMaximumDrawdown
    volatility: StrategyVolatility
    sharpe_ratio: StrategySharpeRatio


def calculate_backtest_benchmarks(
    *,
    trading_dates: Sequence[date],
    active_etfs: Sequence[ETFInfo],
    price_panel: dict[int, list[MarketPrice]],
    transaction_cost_bps: Decimal | float,
    risk_free_rate: Decimal,
    following_trading_date: date | None = None,
) -> list[BacktestBenchmarkResult]:
    if not trading_dates:
        return []
    csi_300 = _resolve_csi_300(active_etfs, first_date=trading_dates[0])
    _validate_prices(trading_dates, [*active_etfs], price_panel)
    return [
        _result(
            key="equal_weight_monthly",
            name="Equal-weight monthly rebalanced portfolio",
            points=_equal_weight_points(
                trading_dates,
                active_etfs,
                price_panel,
                Decimal(str(transaction_cost_bps)),
                following_trading_date,
            ),
            risk_free_rate=risk_free_rate,
        ),
        _result(
            key="csi_300_buy_hold",
            name="CSI 300 buy-and-hold",
            points=_buy_hold_points(trading_dates, csi_300, price_panel),
            risk_free_rate=risk_free_rate,
        ),
    ]


def _resolve_csi_300(active_etfs: Sequence[ETFInfo], *, first_date: date) -> ETFInfo:
    matches = [etf for etf in active_etfs if etf.exchange == "SSE" and etf.symbol == "510300"]
    if len(matches) != 1:
        raise BacktestDataError("Benchmark requires exactly one active SSE:510300 ETF")
    if matches[0].inception_date is not None and matches[0].inception_date > first_date:
        raise BacktestDataError(
            f"Benchmark requires active SSE:510300 ETF on {first_date.isoformat()}"
        )
    return matches[0]


def _validate_prices(
    trading_dates: Sequence[date],
    active_etfs: Sequence[ETFInfo],
    price_panel: dict[int, list[MarketPrice]],
) -> None:
    available = {
        (price.etf_id, price.trade_date) for rows in price_panel.values() for price in rows
    }
    gaps = [
        (etf, trade_date)
        for etf in active_etfs
        for trade_date in trading_dates
        if etf.inception_date is None or etf.inception_date <= trade_date
        if (etf.id, trade_date) not in available
    ]
    if gaps:
        etf, trade_date = gaps[0]
        raise BacktestDataError(
            f"Benchmark requires price for {etf.exchange}:{etf.symbol} on {trade_date.isoformat()}"
        )


def _equal_weight_points(
    trading_dates: Sequence[date],
    active_etfs: Sequence[ETFInfo],
    price_panel: dict[int, list[MarketPrice]],
    transaction_cost_bps: Decimal,
    following_trading_date: date | None,
) -> list[StrategyEquityCurvePoint]:
    initial_etfs = _eligible_etfs(active_etfs, trading_dates[0])
    values = {etf.id: Decimal("1") / Decimal(len(initial_etfs)) for etf in initial_etfs}
    points = [StrategyEquityCurvePoint(trading_dates[0], Decimal("1.000000"), Decimal("0.000000"))]
    cost_rate = transaction_cost_bps / _BASIS_POINTS
    for index, current_date in enumerate(trading_dates[1:], start=1):
        previous_total = sum(values.values(), Decimal("0"))
        values = _mark(values, trading_dates[index - 1], current_date, price_panel)
        total = sum(values.values(), Decimal("0"))
        next_date = (
            trading_dates[index + 1] if index + 1 < len(trading_dates) else following_trading_date
        )
        if _is_month_end(current_date, next_date):
            target_etfs = _eligible_etfs(active_etfs, current_date)
            target = Decimal("1") / Decimal(len(target_etfs))
            target_weights = {etf.id: target for etf in target_etfs}
            actual_weights = {etf_id: value / total for etf_id, value in values.items()}
            turnover = sum(
                abs(
                    actual_weights.get(etf_id, Decimal("0"))
                    - target_weights.get(etf_id, Decimal("0"))
                )
                for etf_id in actual_weights.keys() | target_weights.keys()
            )
            total *= Decimal("1") - turnover * cost_rate
            if total <= 0:
                raise ValueError("Transaction costs exhausted benchmark assets")
            values = {etf_id: total * weight for etf_id, weight in target_weights.items()}
        points.append(
            StrategyEquityCurvePoint(
                current_date,
                total.quantize(_SIX_PLACES),
                (total / previous_total - 1).quantize(_SIX_PLACES),
            )
        )
    return points


def _buy_hold_points(
    trading_dates: Sequence[date],
    etf: ETFInfo,
    price_panel: dict[int, list[MarketPrice]],
) -> list[StrategyEquityCurvePoint]:
    values = {etf.id: Decimal("1")}
    points = [StrategyEquityCurvePoint(trading_dates[0], Decimal("1.000000"), Decimal("0.000000"))]
    for index, current_date in enumerate(trading_dates[1:], start=1):
        previous_total = values[etf.id]
        values = _mark(values, trading_dates[index - 1], current_date, price_panel)
        total = values[etf.id]
        points.append(
            StrategyEquityCurvePoint(
                current_date,
                total.quantize(_SIX_PLACES),
                (total / previous_total - 1).quantize(_SIX_PLACES),
            )
        )
    return points


def _mark(
    values: dict[int, Decimal],
    previous_date: date,
    current_date: date,
    price_panel: dict[int, list[MarketPrice]],
) -> dict[int, Decimal]:
    prices = {
        (price.etf_id, price.trade_date): price for rows in price_panel.values() for price in rows
    }
    marked: dict[int, Decimal] = {}
    for etf_id, value in values.items():
        previous, current = prices[(etf_id, previous_date)], prices[(etf_id, current_date)]
        previous_price, current_price = (
            row.price
            for row in forward_adjusted_prices([previous, current], rebalance_date=current_date)
        )
        marked[etf_id] = value * current_price / previous_price
    return marked


def _is_month_end(current_date: date, next_date: date | None) -> bool:
    return next_date is not None and (current_date.year, current_date.month) != (
        next_date.year,
        next_date.month,
    )


def _eligible_etfs(active_etfs: Sequence[ETFInfo], trade_date: date) -> list[ETFInfo]:
    return [
        etf for etf in active_etfs if etf.inception_date is None or etf.inception_date <= trade_date
    ]


def _result(
    *, key: str, name: str, points: list[StrategyEquityCurvePoint], risk_free_rate: Decimal
) -> BacktestBenchmarkResult:
    return BacktestBenchmarkResult(
        key=key,
        name=name,
        points=points,
        annualized_return=calculate_strategy_annualized_return(points),
        maximum_drawdown=calculate_strategy_maximum_drawdown(points),
        volatility=calculate_strategy_volatility(points),
        sharpe_ratio=calculate_strategy_sharpe_ratio(points, risk_free_rate=risk_free_rate),
    )

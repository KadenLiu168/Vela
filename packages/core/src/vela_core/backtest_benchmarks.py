from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import TypeAlias

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.benchmark_regime_metrics import calculate_benchmark_regime_metrics
from vela_core.errors import BacktestDataError
from vela_core.models import ETFInfo, MarketPrice
from vela_core.resolved_session_price import ResolvedSessionPrice
from vela_core.strategy_equity_curve import (
    ActiveRiskMetrics,
    StrategyAnnualizedReturn,
    StrategyCalmarRatio,
    StrategyEquityCurvePoint,
    StrategyLongestDrawdownDuration,
    StrategyMaximumDrawdown,
    StrategySharpeRatio,
    StrategySortinoRatio,
    StrategyVolatility,
    calculate_active_risk_metrics,
    calculate_strategy_annualized_return,
    calculate_strategy_calmar_ratio,
    calculate_strategy_longest_drawdown_duration,
    calculate_strategy_maximum_drawdown,
    calculate_strategy_sharpe_ratio,
    calculate_strategy_sortino_ratio,
    calculate_strategy_volatility,
)
from vela_core.tail_distribution_risk_metrics import calculate_tail_distribution_risk_metrics

_SIX_PLACES = Decimal("0.000001")
_BASIS_POINTS = Decimal("10000")
_SessionPrice: TypeAlias = MarketPrice | ResolvedSessionPrice


@dataclass(frozen=True)
class BacktestBenchmarkResult:
    key: str
    name: str
    points: list[StrategyEquityCurvePoint]
    annualized_return: StrategyAnnualizedReturn
    maximum_drawdown: StrategyMaximumDrawdown
    volatility: StrategyVolatility
    sharpe_ratio: StrategySharpeRatio
    sortino_ratio: StrategySortinoRatio = StrategySortinoRatio(sortino_ratio=None)
    calmar_ratio: StrategyCalmarRatio = StrategyCalmarRatio(calmar_ratio=None)
    longest_drawdown_duration: StrategyLongestDrawdownDuration = StrategyLongestDrawdownDuration(
        longest_drawdown_duration_sessions=0,
        peak_date=None,
        trough_date=None,
        recovery_date=None,
    )
    tracking_error: Decimal | None = None
    information_ratio: Decimal | None = None
    capm_alpha: Decimal | None = None
    capm_beta: Decimal | None = None
    capm_r_squared: Decimal | None = None
    capm_observation_count: int | None = None
    up_capture_ratio: Decimal | None = None
    up_capture_observation_count: int | None = None
    down_capture_ratio: Decimal | None = None
    down_capture_observation_count: int | None = None
    historical_var_95: Decimal | None = None
    historical_cvar_95: Decimal | None = None
    return_skewness: Decimal | None = None
    return_excess_kurtosis: Decimal | None = None
    distribution_observation_count: int | None = None
    tail_observation_count: int | None = None


def calculate_backtest_benchmarks(
    *,
    trading_dates: Sequence[date],
    active_etfs: Sequence[ETFInfo],
    price_panel: Mapping[int, Sequence[_SessionPrice]],
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


def calculate_backtest_benchmark_active_risk_metrics(
    strategy_points: Sequence[StrategyEquityCurvePoint],
    benchmark: BacktestBenchmarkResult,
) -> BacktestBenchmarkResult:
    active_metrics: ActiveRiskMetrics = calculate_active_risk_metrics(
        strategy_points,
        benchmark.points,
    )
    return replace(
        benchmark,
        tracking_error=active_metrics.tracking_error,
        information_ratio=active_metrics.information_ratio,
    )


def calculate_backtest_benchmark_regime_metrics(
    strategy_points: Sequence[StrategyEquityCurvePoint],
    benchmark: BacktestBenchmarkResult,
    *,
    risk_free_rate: Decimal,
) -> BacktestBenchmarkResult:
    regime_metrics = calculate_benchmark_regime_metrics(
        strategy_points,
        benchmark.points,
        risk_free_rate=risk_free_rate,
        benchmark_key=benchmark.key,
    )
    return replace(
        benchmark,
        capm_alpha=regime_metrics.capm_alpha,
        capm_beta=regime_metrics.capm_beta,
        capm_r_squared=regime_metrics.capm_r_squared,
        capm_observation_count=regime_metrics.capm_observation_count,
        up_capture_ratio=regime_metrics.up_capture_ratio,
        up_capture_observation_count=regime_metrics.up_capture_observation_count,
        down_capture_ratio=regime_metrics.down_capture_ratio,
        down_capture_observation_count=regime_metrics.down_capture_observation_count,
    )


def _resolve_csi_300(active_etfs: Sequence[ETFInfo], *, first_date: date) -> ETFInfo:
    matches = [etf for etf in active_etfs if etf.exchange == "SSE" and etf.symbol == "510300"]
    if len(matches) != 1:
        raise BacktestDataError("Benchmark requires exactly one active SSE:510300 ETF")
    if matches[0].listing_date is None or matches[0].listing_date > first_date:
        raise BacktestDataError(
            f"Benchmark requires active SSE:510300 ETF on {first_date.isoformat()}"
        )
    return matches[0]


def _validate_prices(
    trading_dates: Sequence[date],
    active_etfs: Sequence[ETFInfo],
    price_panel: Mapping[int, Sequence[_SessionPrice]],
) -> None:
    missing_listing = [
        f"{etf.exchange}:{etf.symbol}" for etf in active_etfs if etf.listing_date is None
    ]
    if missing_listing:
        raise BacktestDataError(
            "Benchmark requires listing_date for active ETF " + ", ".join(missing_listing)
        )
    available = {
        (price.etf_id, price.trade_date) for rows in price_panel.values() for price in rows
    }
    gaps = [
        (etf, trade_date)
        for etf in active_etfs
        for trade_date in trading_dates
        if etf.listing_date is None or etf.listing_date <= trade_date
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
    price_panel: Mapping[int, Sequence[_SessionPrice]],
    transaction_cost_bps: Decimal,
    following_trading_date: date | None,
) -> list[StrategyEquityCurvePoint]:
    initial_etfs = _eligible_etfs(active_etfs, trading_dates[0])
    if not initial_etfs:
        raise BacktestDataError("Equal-weight benchmark has no ETF eligible on first session")
    initial_weight = Decimal("1") / Decimal(len(initial_etfs))
    pending_target = {etf.id: initial_weight for etf in initial_etfs}
    cash = Decimal("1")
    values: dict[int, Decimal] = {}
    points: list[StrategyEquityCurvePoint] = []
    cost_rate = transaction_cost_bps / _BASIS_POINTS
    for index, current_date in enumerate(trading_dates):
        previous_total = cash + sum(values.values(), Decimal("0"))
        if index > 0:
            values = _mark(values, trading_dates[index - 1], current_date, price_panel)
        total = cash + sum(values.values(), Decimal("0"))
        next_date = (
            trading_dates[index + 1] if index + 1 < len(trading_dates) else following_trading_date
        )
        if index > 0 and _is_month_end(current_date, next_date):
            target_etfs = _eligible_etfs(active_etfs, current_date)
            if not target_etfs:
                raise BacktestDataError(
                    f"Equal-weight benchmark has no ETF eligible on {current_date.isoformat()}"
                )
            target = Decimal("1") / Decimal(len(target_etfs))
            pending_target = {etf.id: target for etf in target_etfs}
        if pending_target and _target_is_tradable(
            values, pending_target, current_date, price_panel
        ):
            if not values:
                cash, values = _allocate_target_weights(total, pending_target)
            else:
                cash, values = _rebalance_target(
                    total,
                    values,
                    pending_target,
                    cost_rate,
                )
            pending_target = {}
            total = cash + sum(values.values(), Decimal("0"))
        daily_return = Decimal("0") if index == 0 else total / previous_total - 1
        points.append(
            StrategyEquityCurvePoint(
                current_date,
                total.quantize(_SIX_PLACES),
                daily_return.quantize(_SIX_PLACES),
            )
        )
    return points


def _buy_hold_points(
    trading_dates: Sequence[date],
    etf: ETFInfo,
    price_panel: Mapping[int, Sequence[_SessionPrice]],
) -> list[StrategyEquityCurvePoint]:
    cash = Decimal("1")
    values: dict[int, Decimal] = {}
    pending = True
    points: list[StrategyEquityCurvePoint] = []
    for index, current_date in enumerate(trading_dates):
        previous_total = cash + sum(values.values(), Decimal("0"))
        if index > 0:
            values = _mark(values, trading_dates[index - 1], current_date, price_panel)
        total = cash + sum(values.values(), Decimal("0"))
        if pending and _target_is_tradable(
            values,
            {etf.id: Decimal("1")},
            current_date,
            price_panel,
        ):
            cash, values = _allocate_target_weights(total, {etf.id: Decimal("1")})
            pending = False
            total = cash + sum(values.values(), Decimal("0"))
        points.append(
            StrategyEquityCurvePoint(
                current_date,
                total.quantize(_SIX_PLACES),
                (Decimal("0") if index == 0 else total / previous_total - 1).quantize(_SIX_PLACES),
            )
        )
    return points


def _mark(
    values: dict[int, Decimal],
    previous_date: date,
    current_date: date,
    price_panel: Mapping[int, Sequence[_SessionPrice]],
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
        etf
        for etf in active_etfs
        if etf.listing_date is not None and etf.listing_date <= trade_date
    ]


def _target_is_tradable(
    current_values: dict[int, Decimal],
    target_weights: dict[int, Decimal],
    trade_date: date,
    price_panel: Mapping[int, Sequence[_SessionPrice]],
) -> bool:
    prices = {
        (price.etf_id, price.trade_date): price for rows in price_panel.values() for price in rows
    }
    total_assets = sum(current_values.values(), Decimal("0"))
    actual_weights = (
        {}
        if not current_values
        else {etf_id: value / total_assets for etf_id, value in current_values.items()}
    )
    changed_etf_ids = {
        etf_id
        for etf_id in current_values.keys() | target_weights.keys()
        if actual_weights.get(etf_id, Decimal("0")) != target_weights.get(etf_id, Decimal("0"))
    }
    for etf_id in changed_etf_ids:
        price = prices.get((etf_id, trade_date))
        if price is None:
            raise BacktestDataError(f"Benchmark requires price for ETF {etf_id} on {trade_date}")
        if isinstance(price, ResolvedSessionPrice) and not price.tradable:
            return False
    return True


def _allocate_target_weights(
    total_assets: Decimal, target_weights: dict[int, Decimal]
) -> tuple[Decimal, dict[int, Decimal]]:
    return Decimal("0"), {
        etf_id: total_assets * weight for etf_id, weight in target_weights.items()
    }


def _rebalance_target(
    total_assets: Decimal,
    current_values: dict[int, Decimal],
    target_weights: dict[int, Decimal],
    transaction_cost_rate: Decimal,
) -> tuple[Decimal, dict[int, Decimal]]:
    actual_weights = {etf_id: value / total_assets for etf_id, value in current_values.items()}
    turnover = sum(
        abs(actual_weights.get(etf_id, Decimal("0")) - target_weights.get(etf_id, Decimal("0")))
        for etf_id in actual_weights.keys() | target_weights.keys()
    )
    total_after_cost = total_assets * (Decimal("1") - turnover * transaction_cost_rate)
    if total_after_cost <= 0:
        raise ValueError("Transaction costs exhausted benchmark assets")
    return _allocate_target_weights(total_after_cost, target_weights)


def _result(
    *, key: str, name: str, points: list[StrategyEquityCurvePoint], risk_free_rate: Decimal
) -> BacktestBenchmarkResult:
    annualized_return = calculate_strategy_annualized_return(points)
    maximum_drawdown = calculate_strategy_maximum_drawdown(points)
    tail_metrics = calculate_tail_distribution_risk_metrics(points)
    return BacktestBenchmarkResult(
        key=key,
        name=name,
        points=points,
        annualized_return=annualized_return,
        maximum_drawdown=maximum_drawdown,
        volatility=calculate_strategy_volatility(points),
        sharpe_ratio=calculate_strategy_sharpe_ratio(points, risk_free_rate=risk_free_rate),
        sortino_ratio=calculate_strategy_sortino_ratio(points, risk_free_rate=risk_free_rate),
        calmar_ratio=calculate_strategy_calmar_ratio(
            annualized_return.annualized_return,
            maximum_drawdown.max_drawdown,
        ),
        longest_drawdown_duration=calculate_strategy_longest_drawdown_duration(points),
        historical_var_95=tail_metrics.historical_var_95,
        historical_cvar_95=tail_metrics.historical_cvar_95,
        return_skewness=tail_metrics.return_skewness,
        return_excess_kurtosis=tail_metrics.return_excess_kurtosis,
        distribution_observation_count=tail_metrics.observation_count,
        tail_observation_count=tail_metrics.tail_observation_count,
    )

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TypeAlias

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.adjusted_price_projection import forward_adjusted_prices
from vela_core.models import MarketPrice
from vela_core.portfolio_holdings import PortfolioHoldingSnapshot, calculate_portfolio_holdings
from vela_core.strategy_config import StrategyConfig

_SIX_PLACES = Decimal("0.000001")
_BASIS_POINTS = Decimal("10000")
_PriceKey: TypeAlias = tuple[int, date]


@dataclass(frozen=True)
class StrategyEquityCurvePoint:
    trade_date: date
    net_value: Decimal
    daily_return: Decimal


@dataclass(frozen=True)
class StrategyAnnualizedReturn:
    total_return: Decimal | None
    annualized_return: Decimal | None


@dataclass(frozen=True)
class StrategyMaximumDrawdown:
    max_drawdown: Decimal
    peak_date: date | None
    trough_date: date | None


@dataclass(frozen=True)
class StrategyVolatility:
    volatility: Decimal | None


@dataclass(frozen=True)
class StrategySharpeRatio:
    sharpe_ratio: Decimal | None


def calculate_strategy_equity_curve(
    session: Session,
    *,
    trading_dates: list[date],
    strategy_config: StrategyConfig,
) -> list[StrategyEquityCurvePoint]:
    if not trading_dates:
        return []

    holding_snapshots = calculate_portfolio_holdings(
        session,
        trading_dates=trading_dates,
        strategy_id=strategy_config.strategy_id,
        config_version=strategy_config.version,
    )
    prices_by_key = _load_prices_by_key(session, holding_snapshots)
    transaction_cost_rate = Decimal(str(strategy_config.costs.transaction_cost_bps)) / _BASIS_POINTS

    points = [
        StrategyEquityCurvePoint(
            trade_date=trading_dates[0],
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        )
    ]
    net_value = Decimal("1.000000")

    for index, snapshot in enumerate(holding_snapshots[1:], start=1):
        # Point i closes interval i-1 to i: prior holdings earn market return and the
        # snapshot transition at i incurs turnover.
        daily_return = _calculate_daily_return(
            snapshot=snapshot,
            previous_snapshot=holding_snapshots[index - 1],
            previous_date=trading_dates[index - 1],
            prices_by_key=prices_by_key,
            transaction_cost_rate=transaction_cost_rate,
        )
        net_value = (net_value * (Decimal("1") + daily_return)).quantize(_SIX_PLACES)
        points.append(
            StrategyEquityCurvePoint(
                trade_date=snapshot.trade_date,
                net_value=net_value,
                daily_return=daily_return.quantize(_SIX_PLACES),
            )
        )

    return points


def calculate_strategy_annualized_return(
    points: list[StrategyEquityCurvePoint],
) -> StrategyAnnualizedReturn:
    if len(points) < 2:
        return StrategyAnnualizedReturn(total_return=None, annualized_return=None)

    start = points[0]
    end = points[-1]
    elapsed_days = (end.trade_date - start.trade_date).days
    if elapsed_days <= 0 or start.net_value <= 0:
        return StrategyAnnualizedReturn(total_return=None, annualized_return=None)

    total_return = (end.net_value / start.net_value - Decimal("1")).quantize(_SIX_PLACES)
    annualization_power = Decimal("365") / Decimal(elapsed_days)
    annualized_return = (
        Decimal(str(float(end.net_value / start.net_value) ** float(annualization_power)))
        - Decimal("1")
    ).quantize(_SIX_PLACES)

    return StrategyAnnualizedReturn(
        total_return=total_return,
        annualized_return=annualized_return,
    )


def calculate_strategy_maximum_drawdown(
    points: list[StrategyEquityCurvePoint],
) -> StrategyMaximumDrawdown:
    if not points:
        return _zero_maximum_drawdown()

    peak = points[0]
    max_drawdown = Decimal("0.000000")
    peak_date: date | None = None
    trough_date: date | None = None

    for point in points:
        if point.net_value > peak.net_value:
            peak = point

        if peak.net_value <= 0:
            continue

        drawdown = (point.net_value / peak.net_value - Decimal("1")).quantize(_SIX_PLACES)
        if drawdown < max_drawdown:
            max_drawdown = drawdown
            peak_date = peak.trade_date
            trough_date = point.trade_date

    return StrategyMaximumDrawdown(
        max_drawdown=max_drawdown,
        peak_date=peak_date,
        trough_date=trough_date,
    )


def calculate_strategy_volatility(points: list[StrategyEquityCurvePoint]) -> StrategyVolatility:
    effective_returns = [point.daily_return for point in points[1:]]
    if len(effective_returns) < 2:
        return StrategyVolatility(volatility=None)

    mean_return = sum(effective_returns, Decimal("0")) / Decimal(len(effective_returns))
    variance = sum(
        ((daily_return - mean_return) * (daily_return - mean_return))
        for daily_return in effective_returns
    ) / Decimal(len(effective_returns))
    annualized_volatility = Decimal(str((float(variance) ** 0.5) * (252**0.5))).quantize(
        _SIX_PLACES
    )

    return StrategyVolatility(volatility=annualized_volatility)


def calculate_strategy_sharpe_ratio(
    points: list[StrategyEquityCurvePoint],
    *,
    risk_free_rate: Decimal,
) -> StrategySharpeRatio:
    # Effective observations exclude the initial placeholder return
    # (points[0].daily_return == 0.000000 is an initialization artifact).
    effective_returns = [point.daily_return for point in points[1:]]
    if len(effective_returns) < 2:
        return StrategySharpeRatio(sharpe_ratio=None)

    # Arithmetic daily risk-free rate, consistent with the 252 trading-day
    # convention used for volatility annualization.
    daily_risk_free_rate = risk_free_rate / Decimal("252")
    excess_returns = [daily_return - daily_risk_free_rate for daily_return in effective_returns]
    # Population standard deviation is zero iff all excess returns are equal.
    # Comparing the excess values directly (rather than the Decimal variance,
    # which can carry division rounding error from the mean) keeps this
    # boundary exact even when every effective daily return is identical.
    if all(excess == excess_returns[0] for excess in excess_returns):
        return StrategySharpeRatio(sharpe_ratio=None)

    mean_excess = sum(excess_returns, Decimal("0")) / Decimal(len(excess_returns))
    # Population variance: the backtest return sequence is the full realized
    # population being summarized, not a sample (matches volatility).
    variance = sum(
        (excess - mean_excess) * (excess - mean_excess) for excess in excess_returns
    ) / Decimal(len(excess_returns))

    sharpe_ratio = Decimal(
        str(float(mean_excess) / (float(variance) ** 0.5) * (252**0.5))
    ).quantize(_SIX_PLACES)
    return StrategySharpeRatio(sharpe_ratio=sharpe_ratio)


def _load_prices_by_key(
    session: Session,
    holding_snapshots: list[PortfolioHoldingSnapshot],
) -> dict[_PriceKey, MarketPrice]:
    etf_ids = {holding.etf_id for snapshot in holding_snapshots for holding in snapshot.holdings}
    trade_dates = {snapshot.trade_date for snapshot in holding_snapshots}

    if not etf_ids or not trade_dates:
        return {}

    prices = session.scalars(
        select(MarketPrice)
        .where(MarketPrice.etf_id.in_(etf_ids))
        .where(MarketPrice.trade_date.in_(trade_dates))
    ).all()

    return {(price.etf_id, price.trade_date): price for price in prices}


def _calculate_daily_return(
    *,
    snapshot: PortfolioHoldingSnapshot,
    previous_snapshot: PortfolioHoldingSnapshot,
    previous_date: date,
    prices_by_key: dict[_PriceKey, MarketPrice],
    transaction_cost_rate: Decimal,
) -> Decimal:
    daily_return = Decimal("0")

    for holding in previous_snapshot.holdings:
        previous_row = prices_by_key.get((holding.etf_id, previous_date))
        current_row = prices_by_key.get((holding.etf_id, snapshot.trade_date))
        if previous_row is None or current_row is None:
            continue
        previous_price, current_price = (
            price.price
            for price in forward_adjusted_prices(
                [previous_row, current_row],
                rebalance_date=snapshot.trade_date,
            )
        )

        daily_return += holding.target_weight * (current_price / previous_price - Decimal("1"))

    turnover = _calculate_turnover(previous_snapshot, snapshot)
    return daily_return - turnover * transaction_cost_rate


def _calculate_turnover(
    previous_snapshot: PortfolioHoldingSnapshot,
    current_snapshot: PortfolioHoldingSnapshot,
) -> Decimal:
    previous_weights = {
        holding.etf_id: holding.target_weight for holding in previous_snapshot.holdings
    }
    current_weights = {
        holding.etf_id: holding.target_weight for holding in current_snapshot.holdings
    }
    etf_ids = previous_weights.keys() | current_weights.keys()

    return sum(
        (
            abs(
                current_weights.get(etf_id, Decimal("0"))
                - previous_weights.get(etf_id, Decimal("0"))
            )
            for etf_id in etf_ids
        ),
        Decimal("0"),
    )


def _zero_maximum_drawdown() -> StrategyMaximumDrawdown:
    return StrategyMaximumDrawdown(
        max_drawdown=Decimal("0.000000"),
        peak_date=None,
        trough_date=None,
    )

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TypeAlias

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice
from vela_core.portfolio_holdings import PortfolioHoldingSnapshot, calculate_portfolio_holdings

_SIX_PLACES = Decimal("0.000001")
_PriceKey: TypeAlias = tuple[int, date]


@dataclass(frozen=True)
class StrategyEquityCurvePoint:
    trade_date: date
    net_value: Decimal
    daily_return: Decimal


def calculate_strategy_equity_curve(
    session: Session,
    *,
    trading_dates: list[date],
    config_version: str,
) -> list[StrategyEquityCurvePoint]:
    if not trading_dates:
        return []

    holding_snapshots = calculate_portfolio_holdings(
        session,
        trading_dates=trading_dates,
        config_version=config_version,
    )
    prices_by_key = _load_prices_by_key(session, holding_snapshots)

    points = [
        StrategyEquityCurvePoint(
            trade_date=trading_dates[0],
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        )
    ]
    net_value = Decimal("1.000000")

    for index, snapshot in enumerate(holding_snapshots[1:], start=1):
        daily_return = _calculate_daily_return(
            snapshot=snapshot,
            previous_date=trading_dates[index - 1],
            prices_by_key=prices_by_key,
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


def _load_prices_by_key(
    session: Session,
    holding_snapshots: list[PortfolioHoldingSnapshot],
) -> dict[_PriceKey, Decimal]:
    etf_ids = {holding.etf_id for snapshot in holding_snapshots for holding in snapshot.holdings}
    trade_dates = {snapshot.trade_date for snapshot in holding_snapshots}

    if not etf_ids or not trade_dates:
        return {}

    prices = session.scalars(
        select(MarketPrice)
        .where(MarketPrice.etf_id.in_(etf_ids))
        .where(MarketPrice.trade_date.in_(trade_dates))
    ).all()

    return {(price.etf_id, price.trade_date): price.strategy_price for price in prices}


def _calculate_daily_return(
    *,
    snapshot: PortfolioHoldingSnapshot,
    previous_date: date,
    prices_by_key: dict[_PriceKey, Decimal],
) -> Decimal:
    daily_return = Decimal("0")

    for holding in snapshot.holdings:
        previous_price = prices_by_key.get((holding.etf_id, previous_date))
        current_price = prices_by_key.get((holding.etf_id, snapshot.trade_date))
        if previous_price is None or current_price is None:
            continue

        daily_return += holding.target_weight * (current_price / previous_price - Decimal("1"))

    return daily_return

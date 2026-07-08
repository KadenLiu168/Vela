from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice


@dataclass(frozen=True)
class MarketPriceMovingAverage:
    etf_id: int
    as_of_date: date
    window: int
    ma: Decimal | None


def calculate_market_price_moving_average(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
    window: int,
) -> MarketPriceMovingAverage:
    prices = list(
        session.scalars(
            select(MarketPrice)
            .where(MarketPrice.etf_id == etf_id)
            .where(MarketPrice.trade_date <= as_of_date)
            .order_by(MarketPrice.trade_date.desc())
            .limit(window)
        )
    )

    if len(prices) < window or prices[0].trade_date != as_of_date:
        return MarketPriceMovingAverage(
            etf_id=etf_id,
            as_of_date=as_of_date,
            window=window,
            ma=None,
        )

    return MarketPriceMovingAverage(
        etf_id=etf_id,
        as_of_date=as_of_date,
        window=window,
        ma=sum((price.strategy_price for price in prices), Decimal("0"))
        / Decimal(window),
    )
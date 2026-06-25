from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice

MOVING_AVERAGE_WINDOW = 120


@dataclass(frozen=True)
class MarketPriceMovingAverage:
    etf_id: int
    as_of_date: date
    ma_120d: Decimal | None


def calculate_market_price_moving_average(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
) -> MarketPriceMovingAverage:
    prices = list(
        session.scalars(
            select(MarketPrice)
            .where(MarketPrice.etf_id == etf_id)
            .where(MarketPrice.trade_date <= as_of_date)
            .order_by(MarketPrice.trade_date.desc())
            .limit(MOVING_AVERAGE_WINDOW)
        )
    )

    if len(prices) < MOVING_AVERAGE_WINDOW or prices[0].trade_date != as_of_date:
        return MarketPriceMovingAverage(
            etf_id=etf_id,
            as_of_date=as_of_date,
            ma_120d=None,
        )

    return MarketPriceMovingAverage(
        etf_id=etf_id,
        as_of_date=as_of_date,
        ma_120d=sum((price.strategy_price for price in prices), Decimal("0"))
        / Decimal(MOVING_AVERAGE_WINDOW),
    )

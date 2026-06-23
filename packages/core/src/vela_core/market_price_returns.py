from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice

RETURN_WINDOWS = (20, 60, 120)


@dataclass(frozen=True)
class MarketPriceReturns:
    etf_id: int
    as_of_date: date
    return_20d: Decimal | None
    return_60d: Decimal | None
    return_120d: Decimal | None


def calculate_market_price_returns(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
) -> MarketPriceReturns:
    prices = list(
        session.scalars(
            select(MarketPrice)
            .where(MarketPrice.etf_id == etf_id)
            .where(MarketPrice.trade_date <= as_of_date)
            .order_by(MarketPrice.trade_date.desc())
            .limit(max(RETURN_WINDOWS) + 1)
        )
    )

    if not prices or prices[0].trade_date != as_of_date:
        return MarketPriceReturns(
            etf_id=etf_id,
            as_of_date=as_of_date,
            return_20d=None,
            return_60d=None,
            return_120d=None,
        )

    return MarketPriceReturns(
        etf_id=etf_id,
        as_of_date=as_of_date,
        return_20d=_calculate_window_return(prices, 20),
        return_60d=_calculate_window_return(prices, 60),
        return_120d=_calculate_window_return(prices, 120),
    )


def _calculate_window_return(
    prices: list[MarketPrice],
    window: int,
) -> Decimal | None:
    if len(prices) <= window:
        return None

    current_price = prices[0].strategy_price
    prior_price = prices[window].strategy_price
    return current_price / prior_price - Decimal("1")

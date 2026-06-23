from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.market_price_moving_average import calculate_market_price_moving_average
from vela_core.models import MarketPrice
from vela_core.strategy_config import StrategyConfig


@dataclass(frozen=True)
class TrendFilterResult:
    etf_id: int
    as_of_date: date
    current_price: Decimal | None
    moving_average: Decimal | None
    passes_filter: bool


def apply_trend_filter(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
    config: StrategyConfig,
) -> TrendFilterResult:
    current_market_price = session.scalar(
        select(MarketPrice)
        .where(MarketPrice.etf_id == etf_id)
        .where(MarketPrice.trade_date == as_of_date)
    )
    current_price = (
        current_market_price.strategy_price if current_market_price is not None else None
    )
    moving_average = calculate_market_price_moving_average(
        session,
        etf_id=etf_id,
        as_of_date=as_of_date,
    )

    moving_average_days = config.trend_filter.moving_average_days
    price_relation = config.trend_filter.price_relation
    passes_filter = (
        moving_average_days == 120
        and price_relation == "above"
        and current_price is not None
        and moving_average.ma_120d is not None
        and current_price > moving_average.ma_120d
    )

    return TrendFilterResult(
        etf_id=etf_id,
        as_of_date=as_of_date,
        current_price=current_price,
        moving_average=moving_average.ma_120d,
        passes_filter=passes_filter,
    )

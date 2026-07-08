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
    window = config.trend_filter.moving_average_days
    relation = config.trend_filter.price_relation
    moving_average = calculate_market_price_moving_average(
        session,
        etf_id=etf_id,
        as_of_date=as_of_date,
        window=window,
    )
    ma_value = moving_average.ma

    passes_filter = (
        current_price is not None
        and ma_value is not None
        and (
            (relation == "above" and current_price > ma_value)
            or (relation == "below" and current_price < ma_value)
        )
    )

    return TrendFilterResult(
        etf_id=etf_id,
        as_of_date=as_of_date,
        current_price=current_price,
        moving_average=ma_value,
        passes_filter=passes_filter,
    )
from vela_core.market_data_provider import DailyPrice
from vela_core.models import MarketPrice


def to_market_price(daily_price: DailyPrice, *, etf_id: int) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=daily_price.trade_date,
        open_price=daily_price.open_price,
        high_price=daily_price.high_price,
        low_price=daily_price.low_price,
        close_price=daily_price.close_price,
        adjusted_close=daily_price.adjusted_close,
        volume=daily_price.volume,
    )

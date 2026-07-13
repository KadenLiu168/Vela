from datetime import date
from decimal import Decimal

from vela_core import DailyPrice, to_market_price


def test_daily_price_maps_to_market_price_fields() -> None:
    daily_price = DailyPrice(
        symbol="513500",
        trade_date=date(2026, 6, 18),
        open_price=Decimal("1.230"),
        high_price=Decimal("1.260"),
        low_price=Decimal("1.220"),
        close_price=Decimal("1.250"),
        factor=Decimal("1.240"),
        volume=1000,
    )

    market_price = to_market_price(daily_price, etf_id=42)

    assert market_price.etf_id == 42
    assert market_price.trade_date == date(2026, 6, 18)
    assert market_price.open_price == Decimal("1.230")
    assert market_price.high_price == Decimal("1.260")
    assert market_price.low_price == Decimal("1.220")
    assert market_price.close_price == Decimal("1.250")
    assert market_price.factor_hfq == Decimal("1.240")
    assert market_price.volume == 1000
    assert type(market_price.factor_hfq) is Decimal
    assert type(market_price.volume) is int


def test_daily_price_mapping_preserves_explicit_field_types() -> None:
    daily_price = DailyPrice(
        symbol="513500",
        trade_date=date(2026, 6, 18),
        open_price=Decimal("1.230"),
        high_price=Decimal("1.260"),
        low_price=Decimal("1.220"),
        close_price=Decimal("1.250"),
        factor=Decimal("1.0"),
        volume=None,
    )

    market_price = to_market_price(daily_price, etf_id=42)

    assert type(market_price.trade_date) is date
    assert type(market_price.open_price) is Decimal
    assert type(market_price.high_price) is Decimal
    assert type(market_price.low_price) is Decimal
    assert type(market_price.close_price) is Decimal
    assert type(market_price.factor_hfq) is Decimal
    assert market_price.volume is None

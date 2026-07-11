from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
from vela_core import AkShareMarketDataProvider, DailyPrice, to_market_price


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


def test_akshare_daily_rows_normalize_then_map_to_market_price() -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(
            pd.DataFrame(
                [
                    {
                        "日期": "2026-06-18",
                        "开盘": "1.230",
                        "最高": "1.260",
                        "最低": "1.220",
                        "收盘": "1.250",
                        "成交量": 1000,
                    }
                ]
            )
        )
    )

    daily_price = provider.get_etf_daily_prices(
        "513500",
        start_date=date(2026, 6, 18),
        end_date=date(2026, 6, 18),
    )[0]
    market_price = to_market_price(daily_price, etf_id=42)

    assert market_price.etf_id == 42
    assert market_price.trade_date == date(2026, 6, 18)
    assert market_price.open_price == Decimal("1.230")
    assert market_price.high_price == Decimal("1.260")
    assert market_price.low_price == Decimal("1.220")
    assert market_price.close_price == Decimal("1.250")
    assert market_price.factor_hfq == Decimal("1.0")
    assert market_price.volume == 1000


class FakeAkShareModule:
    def __init__(self, response: pd.DataFrame) -> None:
        self.response = response

    def fund_etf_hist_em(self, **_: Any) -> pd.DataFrame:
        return self.response

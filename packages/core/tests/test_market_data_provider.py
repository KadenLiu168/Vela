from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from inspect import getsource

import vela_core.market_data_provider as provider_module
from vela_core import DailyPrice, MarketDataProvider


def test_daily_price_exposes_etf_daily_ohlcv_fields() -> None:
    price = DailyPrice(
        symbol="SPY",
        trade_date=date(2026, 6, 18),
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        factor=Decimal("1.0025"),
        volume=1000,
    )

    assert price.symbol == "SPY"
    assert price.trade_date == date(2026, 6, 18)
    assert price.open_price == Decimal("100.00")
    assert price.high_price == Decimal("101.00")
    assert price.low_price == Decimal("99.00")
    assert price.close_price == Decimal("100.50")
    assert price.factor == Decimal("1.0025")
    assert price.volume == 1000


def test_fake_provider_satisfies_market_data_provider_contract() -> None:
    expected_price = DailyPrice(
        symbol="SPY",
        trade_date=date(2026, 6, 18),
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        factor=Decimal("1.0"),
    )
    provider = FakeMarketDataProvider([expected_price])

    assert isinstance(provider, MarketDataProvider)
    assert _fetch_prices(provider, "SPY") == [expected_price]


def test_fake_provider_accepts_optional_date_bounds() -> None:
    inside_range = DailyPrice(
        symbol="SPY",
        trade_date=date(2026, 6, 18),
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        factor=Decimal("1.0"),
    )
    outside_range = DailyPrice(
        symbol="SPY",
        trade_date=date(2026, 6, 17),
        open_price=Decimal("98.00"),
        high_price=Decimal("99.00"),
        low_price=Decimal("97.00"),
        close_price=Decimal("98.50"),
        factor=Decimal("1.0"),
    )
    provider = FakeMarketDataProvider([inside_range, outside_range])

    prices = provider.get_etf_daily_prices(
        "SPY",
        start_date=date(2026, 6, 18),
        end_date=date(2026, 6, 18),
    )

    assert prices == [inside_range]


def test_provider_contract_does_not_depend_on_persistence_or_provider_libraries() -> None:
    source = getsource(provider_module)

    assert "MarketPrice" not in source
    assert "sqlalchemy" not in source
    assert "akshare" not in source
    assert "pandas" not in source


class FakeMarketDataProvider:
    name = "fake"

    def __init__(self, prices: Sequence[DailyPrice]) -> None:
        self._prices = prices

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        return [
            price
            for price in self._prices
            if price.symbol == symbol
            and (start_date is None or price.trade_date >= start_date)
            and (end_date is None or price.trade_date <= end_date)
        ]


def _fetch_prices(provider: MarketDataProvider, symbol: str) -> Sequence[DailyPrice]:
    return provider.get_etf_daily_prices(symbol)

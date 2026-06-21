from datetime import date
from decimal import Decimal
from inspect import getsource
from typing import Any

import pandas as pd
import pytest
import vela_core.market_data_provider as provider_contract_module
from vela_core import AkShareMarketDataProvider, DailyPrice, MarketDataProviderError


def test_akshare_provider_normalizes_etf_daily_ohlcv_fields() -> None:
    akshare = FakeAkShareModule(
        pd.DataFrame(
            [
                {
                    "日期": "2026-06-18",
                    "开盘": "1.230",
                    "收盘": "1.250",
                    "最高": "1.260",
                    "最低": "1.220",
                    "成交量": 1000,
                },
                {
                    "日期": "2026-06-17",
                    "开盘": "1.200",
                    "收盘": "1.210",
                    "最高": "1.220",
                    "最低": "1.190",
                    "成交量": 900,
                },
            ]
        )
    )
    provider = AkShareMarketDataProvider(akshare)

    prices = provider.get_etf_daily_prices(
        "513500",
        start_date=date(2026, 6, 17),
        end_date=date(2026, 6, 18),
    )

    assert prices == [
        DailyPrice(
            symbol="513500",
            trade_date=date(2026, 6, 17),
            open_price=Decimal("1.200"),
            high_price=Decimal("1.220"),
            low_price=Decimal("1.190"),
            close_price=Decimal("1.210"),
            adjusted_close=None,
            volume=900,
        ),
        DailyPrice(
            symbol="513500",
            trade_date=date(2026, 6, 18),
            open_price=Decimal("1.230"),
            high_price=Decimal("1.260"),
            low_price=Decimal("1.220"),
            close_price=Decimal("1.250"),
            adjusted_close=None,
            volume=1000,
        ),
    ]


def test_akshare_provider_uses_daily_unadjusted_request_with_date_bounds() -> None:
    akshare = FakeAkShareModule(_empty_prices())
    provider = AkShareMarketDataProvider(akshare)

    provider.get_etf_daily_prices(
        "513500",
        start_date=date(2026, 1, 2),
        end_date=date(2026, 6, 18),
    )

    assert akshare.calls == [
        {
            "symbol": "513500",
            "period": "daily",
            "start_date": "20260102",
            "end_date": "20260618",
            "adjust": "",
        }
    ]


def test_akshare_provider_uses_default_start_date_when_start_date_is_missing() -> None:
    akshare = FakeAkShareModule(_empty_prices())
    provider = AkShareMarketDataProvider(akshare)

    provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    assert akshare.calls[0]["start_date"] == "20000101"


def test_akshare_provider_normalizes_timestamp_trade_date_to_date() -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(
            pd.DataFrame(
                [
                    {
                        "日期": pd.Timestamp("2026-06-18 00:00:00"),
                        "开盘": "1.230",
                        "收盘": "1.250",
                        "最高": "1.260",
                        "最低": "1.220",
                        "成交量": 1000,
                    }
                ]
            )
        )
    )

    price = provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))[0]

    assert price.trade_date == date(2026, 6, 18)
    assert type(price.trade_date) is date


def test_akshare_provider_returns_empty_sequence_for_empty_result() -> None:
    provider = AkShareMarketDataProvider(FakeAkShareModule(_empty_prices()))

    assert provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18)) == []


def test_akshare_provider_wraps_source_errors_with_context() -> None:
    provider = AkShareMarketDataProvider(FailingAkShareModule(RuntimeError("timeout")))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    message = str(exc_info.value)
    assert "akshare" in message
    assert "513500" in message
    assert "20260617" in message
    assert "20260618" in message
    assert "timeout" in message


def test_akshare_provider_wraps_missing_columns_with_context() -> None:
    provider = AkShareMarketDataProvider(FakeAkShareModule(pd.DataFrame([{"日期": "2026-06-18"}])))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    message = str(exc_info.value)
    assert "akshare" in message
    assert "513500" in message
    assert "missing required columns" in message


def test_akshare_provider_wraps_row_parsing_errors_with_context() -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(
            pd.DataFrame(
                [
                    {
                        "日期": "not-a-date",
                        "开盘": "1.230",
                        "收盘": "1.250",
                        "最高": "1.260",
                        "最低": "1.220",
                        "成交量": 1000,
                    }
                ]
            )
        )
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    message = str(exc_info.value)
    assert "akshare" in message
    assert "513500" in message
    assert "normalization failed" in message


def test_provider_contract_module_remains_source_library_independent() -> None:
    source = getsource(provider_contract_module)

    assert "akshare" not in source
    assert "pandas" not in source


class FakeAkShareModule:
    def __init__(self, response: pd.DataFrame) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def fund_etf_hist_em(
        self,
        *,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame:
        self.calls.append(
            {
                "symbol": symbol,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "adjust": adjust,
            }
        )
        return self.response


class FailingAkShareModule:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def fund_etf_hist_em(self, **_: str) -> pd.DataFrame:
        raise self.error


def _empty_prices() -> pd.DataFrame:
    return pd.DataFrame(columns=["日期", "开盘", "收盘", "最高", "最低", "成交量"])

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from vela_core import DailyPrice, MarketDataProviderError, TencentMarketDataProvider


class _FakeAkShareModule:
    def __init__(self, response: pd.DataFrame) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def stock_zh_a_hist_tx(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame:
        self.calls.append(
            {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "adjust": adjust,
            }
        )
        return self.response


class _FailingAkShareModule(_FakeAkShareModule):
    def stock_zh_a_hist_tx(self, **kwargs: Any) -> pd.DataFrame:  # type: ignore[override]
        raise RuntimeError("network failure")


class _FlakyAkShareModule(_FakeAkShareModule):
    def __init__(self, *, failures_before_success: int, response: pd.DataFrame) -> None:
        super().__init__(response)
        self._failures_before_success = failures_before_success

    def stock_zh_a_hist_tx(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame:
        self.calls.append(
            {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "adjust": adjust,
            }
        )
        if len(self.calls) <= self._failures_before_success:
            raise RuntimeError("temporary timeout")
        return self.response


@pytest.fixture(autouse=True)
def _disable_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TencentMarketDataProvider._fetch_rows.retry, "sleep", lambda _: None)


def test_tencent_provider_normalizes_etf_daily_ohlc_fields() -> None:
    akshare = _FakeAkShareModule(
        pd.DataFrame(
            [
                {
                    "date": date(2026, 6, 17),
                    "open": "1.200",
                    "close": "1.210",
                    "high": "1.220",
                    "low": "1.190",
                    "amount": 11000.0,
                },
                {
                    "date": date(2026, 6, 18),
                    "open": "1.230",
                    "close": "1.250",
                    "high": "1.260",
                    "low": "1.220",
                    "amount": 12345.0,
                },
            ]
        )
    )
    provider = TencentMarketDataProvider(akshare)

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
            factor=Decimal("1.0"),
            volume=None,
        ),
        DailyPrice(
            symbol="513500",
            trade_date=date(2026, 6, 18),
            open_price=Decimal("1.230"),
            high_price=Decimal("1.260"),
            low_price=Decimal("1.220"),
            close_price=Decimal("1.250"),
            factor=Decimal("1.0"),
            volume=None,
        ),
    ]


def test_tencent_provider_returns_prices_sorted_ascending_by_trade_date() -> None:
    akshare = _FakeAkShareModule(
        pd.DataFrame(
            [
                {
                    "date": date(2026, 6, 19),
                    "open": "1.240",
                    "close": "1.260",
                    "high": "1.270",
                    "low": "1.230",
                    "amount": 14000.0,
                },
                {
                    "date": date(2026, 6, 17),
                    "open": "1.200",
                    "close": "1.210",
                    "high": "1.220",
                    "low": "1.190",
                    "amount": 11000.0,
                },
                {
                    "date": date(2026, 6, 18),
                    "open": "1.230",
                    "close": "1.250",
                    "high": "1.260",
                    "low": "1.220",
                    "amount": 12345.0,
                },
            ]
        )
    )
    provider = TencentMarketDataProvider(akshare)

    prices = provider.get_etf_daily_prices(
        "513500",
        start_date=date(2026, 6, 17),
        end_date=date(2026, 6, 19),
    )

    assert [price.trade_date for price in prices] == [
        date(2026, 6, 17),
        date(2026, 6, 18),
        date(2026, 6, 19),
    ]


def test_tencent_provider_prefixes_symbol_for_sh_market() -> None:
    akshare = _FakeAkShareModule(_empty_prices())
    provider = TencentMarketDataProvider(akshare)

    provider.get_etf_daily_prices(
        "510300",
        start_date=date(2026, 1, 2),
        end_date=date(2026, 6, 18),
    )

    assert akshare.calls == [
        {
            "symbol": "sh510300",
            "start_date": "20260102",
            "end_date": "20260618",
            "adjust": "",
        },
        {
            "symbol": "sh510300",
            "start_date": "20260102",
            "end_date": "20260618",
            "adjust": "hfq",
        },
    ]


def test_tencent_provider_prefixes_symbol_for_sz_market() -> None:
    akshare = _FakeAkShareModule(_empty_prices())
    provider = TencentMarketDataProvider(akshare)

    provider.get_etf_daily_prices(
        "159915",
        start_date=date(2026, 1, 2),
        end_date=date(2026, 6, 18),
    )

    assert akshare.calls == [
        {
            "symbol": "sz159915",
            "start_date": "20260102",
            "end_date": "20260618",
            "adjust": "",
        },
        {
            "symbol": "sz159915",
            "start_date": "20260102",
            "end_date": "20260618",
            "adjust": "hfq",
        },
    ]


def test_tencent_provider_uses_default_start_date_when_start_date_is_missing() -> None:
    akshare = _FakeAkShareModule(_empty_prices())
    provider = TencentMarketDataProvider(akshare)

    provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    assert akshare.calls[0]["start_date"] == "20000101"


def test_tencent_provider_returns_empty_sequence_for_empty_result() -> None:
    provider = TencentMarketDataProvider(_FakeAkShareModule(_empty_prices()))

    assert provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18)) == []


def test_tencent_provider_drops_amount_column() -> None:
    akshare = _FakeAkShareModule(
        pd.DataFrame(
            [
                {
                    "date": date(2026, 6, 18),
                    "open": 1.0,
                    "close": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "amount": 99_999_999.0,
                }
            ]
        )
    )
    provider = TencentMarketDataProvider(akshare)

    price = provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))[0]

    assert price.volume is None
    assert price.factor == Decimal("1.0")


def test_tencent_provider_wraps_source_errors_with_context() -> None:
    provider = TencentMarketDataProvider(_FailingAkShareModule(_empty_prices()))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    message = str(exc_info.value)
    assert "tencent" in message
    assert "513500" in message
    assert "20260617" in message
    assert "20260618" in message
    assert "network failure" in message


def test_tencent_provider_retries_temporary_source_failure() -> None:
    akshare = _FlakyAkShareModule(
        failures_before_success=2,
        response=pd.DataFrame(
            [
                {
                    "date": date(2026, 6, 18),
                    "open": 1.0,
                    "close": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "amount": 100.0,
                }
            ]
        ),
    )
    provider = TencentMarketDataProvider(akshare)

    prices = provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    assert len(prices) == 1
    assert len(akshare.calls) == 4


def test_tencent_provider_raises_after_retry_exhausted() -> None:
    provider = TencentMarketDataProvider(
        _FlakyAkShareModule(failures_before_success=99, response=_empty_prices())
    )

    with pytest.raises(MarketDataProviderError):
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))


def test_tencent_provider_rejects_missing_required_columns() -> None:
    akshare = _FakeAkShareModule(pd.DataFrame([{"date": date(2026, 6, 18), "open": 1.0}]))
    provider = TencentMarketDataProvider(akshare)

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    assert "missing required columns" in str(exc_info.value)


def test_tencent_provider_rejects_missing_date() -> None:
    provider = TencentMarketDataProvider(_FakeAkShareModule(_daily_row(date=None)))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    _assert_validation_context(str(exc_info.value), column="date")


def test_tencent_provider_rejects_invalid_date() -> None:
    provider = TencentMarketDataProvider(_FakeAkShareModule(_daily_row(date="not-a-date")))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    _assert_validation_context(str(exc_info.value), column="date")


def test_tencent_provider_rejects_non_numeric_price() -> None:
    provider = TencentMarketDataProvider(_FakeAkShareModule(_daily_row(open="abc")))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    _assert_validation_context(str(exc_info.value), column="open")


def test_tencent_provider_rejects_negative_price() -> None:
    provider = TencentMarketDataProvider(_FakeAkShareModule(_daily_row(open=-1.0)))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    _assert_validation_context(str(exc_info.value), column="open", value=-1.0)


def test_tencent_provider_rejects_inconsistent_ohlc() -> None:
    provider = TencentMarketDataProvider(
        _FakeAkShareModule(_daily_row(high=0.5))  # high < open/low/close
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    _assert_validation_context(str(exc_info.value), column="ohlc")


def test_tencent_provider_rejects_whole_result_when_one_row_invalid() -> None:
    akshare = _FakeAkShareModule(
        pd.DataFrame(
            [
                {
                    "date": date(2026, 6, 18),
                    "open": "broken",
                    "close": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "amount": 100.0,
                },
                {
                    "date": date(2026, 6, 17),
                    "open": 1.0,
                    "close": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "amount": 100.0,
                },
            ]
        )
    )
    provider = TencentMarketDataProvider(akshare)

    with pytest.raises(MarketDataProviderError):
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))


def test_tencent_provider_name_is_tencent() -> None:
    assert TencentMarketDataProvider().name == "tencent"


def _empty_prices() -> pd.DataFrame:
    return pd.DataFrame(columns=["date", "open", "close", "high", "low", "amount"])


def _daily_row(**overrides: object) -> pd.DataFrame:
    row: dict[str, object] = {
        "date": date(2026, 6, 18),
        "open": "1.230",
        "close": "1.250",
        "high": "1.260",
        "low": "1.220",
        "amount": 1000.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _assert_validation_context(
    message: str,
    *,
    column: str,
    value: object | None = None,
    row_index: int = 0,
) -> None:
    assert "tencent" in message
    assert "513500" in message
    assert "20260618" in message
    assert f"row_index={row_index}" in message
    assert f"column={column}" in message
    assert "reason=" in message
    if value is not None:
        assert f"invalid value={value!r}" in message

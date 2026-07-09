from datetime import date
from decimal import Decimal
from inspect import getsource
from typing import Any

import pandas as pd
import pytest
import vela_core.market_data_provider as provider_contract_module
from vela_core import AkShareMarketDataProvider, DailyPrice, MarketDataProviderError


@pytest.fixture(autouse=True)
def _disable_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AkShareMarketDataProvider._fetch_rows.retry, "sleep", lambda _: None)


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


def test_akshare_provider_retries_temporary_source_failure() -> None:
    akshare = TemporarilyFailingAkShareModule(
        failures_before_success=2,
        response=pd.DataFrame([_daily_row()]),
    )
    provider = AkShareMarketDataProvider(akshare)

    prices = provider.get_etf_daily_prices(
        "513500",
        start_date=date(2026, 6, 17),
        end_date=date(2026, 6, 18),
    )

    assert len(prices) == 1
    assert prices[0].symbol == "513500"
    assert len(akshare.calls) == 3


def test_akshare_provider_raises_provider_error_after_retries_are_exhausted() -> None:
    akshare = FailingAkShareModule(RuntimeError("timeout"))
    provider = AkShareMarketDataProvider(akshare)

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
    assert len(akshare.calls) == 3


def test_akshare_provider_wraps_missing_columns_with_context() -> None:
    provider = AkShareMarketDataProvider(FakeAkShareModule(pd.DataFrame([{"日期": "2026-06-18"}])))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("513500", end_date=date(2026, 6, 18))

    message = str(exc_info.value)
    assert "akshare" in message
    assert "513500" in message
    assert "missing required columns" in message


def test_akshare_provider_does_not_retry_invalid_returned_rows() -> None:
    akshare = FakeAkShareModule(pd.DataFrame([_daily_row(开盘="not-a-number")]))
    provider = AkShareMarketDataProvider(akshare)

    with pytest.raises(MarketDataProviderError):
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    assert len(akshare.calls) == 1


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
    assert "row_index=0" in message
    assert "column=日期" in message
    assert "invalid value='not-a-date'" in message


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("日期", None),
        ("日期", ""),
        ("日期", pd.NA),
        ("开盘", None),
        ("开盘", ""),
        ("开盘", float("nan")),
        ("最高", None),
        ("最低", ""),
        ("收盘", pd.NA),
        ("成交量", None),
        ("成交量", ""),
    ],
)
def test_akshare_provider_rejects_missing_required_row_values(
    column: str,
    value: object,
) -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(pd.DataFrame([_daily_row(**{column: value})]))
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    _assert_validation_context(str(exc_info.value), column=column, value=value)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("日期", "not-a-date"),
        ("开盘", "not-a-number"),
        ("最高", "Infinity"),
        ("最低", "-Infinity"),
        ("收盘", "NaN"),
    ],
)
def test_akshare_provider_rejects_invalid_dates_and_decimal_values(
    column: str,
    value: object,
) -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(pd.DataFrame([_daily_row(**{column: value})]))
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    _assert_validation_context(str(exc_info.value), column=column, value=value)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("开盘", "0"),
        ("最高", "-1.00"),
        ("最低", "0.000"),
        ("收盘", "-0.01"),
    ],
)
def test_akshare_provider_rejects_non_positive_ohlc_prices(
    column: str,
    value: object,
) -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(pd.DataFrame([_daily_row(**{column: value})]))
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    _assert_validation_context(str(exc_info.value), column=column, value=value)


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"最高": "1.190"}, "ohlc"),
        ({"最低": "1.260"}, "ohlc"),
    ],
)
def test_akshare_provider_rejects_inconsistent_ohlc_relationships(
    overrides: dict[str, object],
    field: str,
) -> None:
    provider = AkShareMarketDataProvider(FakeAkShareModule(pd.DataFrame([_daily_row(**overrides)])))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    message = str(exc_info.value)
    _assert_validation_context(message, column=field)
    assert "high must be at least" in message or "low must be at most" in message


@pytest.mark.parametrize("value", ["not-a-number", "1.5", "-1"])
def test_akshare_provider_rejects_invalid_volume(value: object) -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(pd.DataFrame([_daily_row(成交量=value)]))
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    _assert_validation_context(str(exc_info.value), column="成交量", value=value)


def test_akshare_provider_rejects_whole_result_when_one_row_is_invalid() -> None:
    provider = AkShareMarketDataProvider(
        FakeAkShareModule(
            pd.DataFrame(
                [
                    _daily_row(日期="2026-06-17"),
                    _daily_row(日期="2026-06-18", 开盘="not-a-number"),
                ]
            )
        )
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "513500",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    _assert_validation_context(
        str(exc_info.value),
        column="开盘",
        value="not-a-number",
        row_index=1,
    )


def test_provider_contract_module_remains_source_library_independent() -> None:
    source = getsource(provider_contract_module)

    assert "akshare" not in source
    assert "pandas" not in source
    assert "jqdatasdk" not in source
    assert "joinquant" not in source


def test_import_vela_core_does_not_require_jqdatasdk() -> None:
    import sys

    import vela_core  # noqa: F401

    assert "jqdatasdk" not in sys.modules


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
        self.calls: list[dict[str, str]] = []

    def fund_etf_hist_em(self, **kwargs: str) -> pd.DataFrame:
        self.calls.append(kwargs)
        raise self.error


class TemporarilyFailingAkShareModule(FakeAkShareModule):
    def __init__(self, *, failures_before_success: int, response: pd.DataFrame) -> None:
        super().__init__(response)
        self._failures_before_success = failures_before_success

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
        if len(self.calls) <= self._failures_before_success:
            raise RuntimeError("temporary timeout")
        return self.response


def _empty_prices() -> pd.DataFrame:
    return pd.DataFrame(columns=["日期", "开盘", "收盘", "最高", "最低", "成交量"])


def _daily_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "日期": "2026-06-18",
        "开盘": "1.230",
        "收盘": "1.250",
        "最高": "1.260",
        "最低": "1.220",
        "成交量": 1000,
    }
    row.update(overrides)
    return row


def _assert_validation_context(
    message: str,
    *,
    column: str,
    value: object | None = None,
    row_index: int = 0,
) -> None:
    assert "akshare" in message
    assert "513500" in message
    assert "20260617" in message
    assert "20260618" in message
    assert f"row_index={row_index}" in message
    assert f"column={column}" in message
    assert "reason=" in message
    if value is not None:
        assert f"invalid value={value!r}" in message

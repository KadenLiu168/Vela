from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
import vela_core.joinquant_market_data_provider as jq_module
from vela_core import DailyPrice, JoinQuantMarketDataProvider, MarketDataProviderError


@pytest.fixture(autouse=True)
def _jq_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JQ_USERNAME", "dummy-user")
    monkeypatch.setenv("JQ_PASSWORD", "dummy-pass")


@pytest.fixture(autouse=True)
def _reset_auth_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jq_module, "_JQ_AUTHENTICATED", False)


@pytest.fixture(autouse=True)
def _disable_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(JoinQuantMarketDataProvider._fetch_rows.retry, "sleep", lambda _: None)


def test_joinquant_provider_normalizes_etf_daily_ohlcv_fields() -> None:
    jq = FakeJoinQuantModule(
        _prices_frame(
            ["2026-06-17", "2026-06-18"],
            open=["1.200", "1.230"],
            high=["1.220", "1.260"],
            low=["1.190", "1.220"],
            close=["1.210", "1.250"],
            volume=[900, 1000],
        )
    )
    provider = JoinQuantMarketDataProvider(jq)

    prices = provider.get_etf_daily_prices(
        "510300",
        start_date=date(2026, 6, 17),
        end_date=date(2026, 6, 18),
    )

    assert prices == [
        DailyPrice(
            symbol="510300",
            trade_date=date(2026, 6, 17),
            open_price=Decimal("1.200"),
            high_price=Decimal("1.220"),
            low_price=Decimal("1.190"),
            close_price=Decimal("1.210"),
            factor=Decimal("1.0"),
            volume=900,
        ),
        DailyPrice(
            symbol="510300",
            trade_date=date(2026, 6, 18),
            open_price=Decimal("1.230"),
            high_price=Decimal("1.260"),
            low_price=Decimal("1.220"),
            close_price=Decimal("1.250"),
            factor=Decimal("1.0"),
            volume=1000,
        ),
    ]


def test_joinquant_provider_promotes_date_index_to_trade_date_column() -> None:
    jq = FakeJoinQuantModule(_prices_frame(["2026-06-18"]))
    provider = JoinQuantMarketDataProvider(jq)

    prices = provider.get_etf_daily_prices("510300", end_date=date(2026, 6, 18))

    # The fake returns rows with an unnamed DatetimeIndex; the provider must
    # name the index `trade_date` so reset_index yields a `trade_date` column
    # that the shared base normalization logic can read.
    assert jq.response.index.name == "trade_date"
    assert len(prices) == 1
    assert prices[0].trade_date == date(2026, 6, 18)


def test_joinquant_provider_maps_symbol_to_xshg_suffix() -> None:
    jq = FakeJoinQuantModule(_empty_prices())
    provider = JoinQuantMarketDataProvider(jq)

    provider.get_etf_daily_prices(
        "510300",
        start_date=date(2026, 1, 2),
        end_date=date(2026, 6, 18),
    )

    assert jq.calls[0]["security"] == "510300.XSHG"


def test_joinquant_provider_maps_symbol_to_xshe_suffix() -> None:
    jq = FakeJoinQuantModule(_empty_prices())
    provider = JoinQuantMarketDataProvider(jq)

    provider.get_etf_daily_prices(
        "159915",
        start_date=date(2026, 1, 2),
        end_date=date(2026, 6, 18),
    )

    assert jq.calls[0]["security"] == "159915.XSHE"


def test_joinquant_provider_forwards_date_bounds_as_iso_strings() -> None:
    jq = FakeJoinQuantModule(_empty_prices())
    provider = JoinQuantMarketDataProvider(jq)

    provider.get_etf_daily_prices(
        "510300",
        start_date=date(2026, 1, 2),
        end_date=date(2026, 6, 18),
    )

    assert jq.calls[0]["start_date"] == "2026-01-02"
    assert jq.calls[0]["end_date"] == "2026-06-18"
    assert jq.calls[0]["frequency"] == "daily"
    assert jq.calls[0]["fq"] is None


def test_joinquant_provider_returns_empty_sequence_for_empty_result() -> None:
    provider = JoinQuantMarketDataProvider(FakeJoinQuantModule(_empty_prices()))

    assert provider.get_etf_daily_prices("510300", end_date=date(2026, 6, 18)) == []


def test_joinquant_provider_returns_prices_sorted_ascending_by_trade_date() -> None:
    jq = FakeJoinQuantModule(
        _prices_frame(
            ["2026-06-19", "2026-06-17", "2026-06-18"],
            open=["1.240", "1.200", "1.230"],
            high=["1.270", "1.220", "1.260"],
            low=["1.230", "1.190", "1.220"],
            close=["1.260", "1.210", "1.250"],
            volume=[1400, 900, 1000],
        )
    )
    provider = JoinQuantMarketDataProvider(jq)

    prices = provider.get_etf_daily_prices(
        "510300",
        start_date=date(2026, 6, 17),
        end_date=date(2026, 6, 19),
    )

    assert [price.trade_date for price in prices] == [
        date(2026, 6, 17),
        date(2026, 6, 18),
        date(2026, 6, 19),
    ]


def test_joinquant_provider_wraps_source_errors_with_context() -> None:
    provider = JoinQuantMarketDataProvider(FailingJoinQuantModule(RuntimeError("timeout")))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "510300",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    message = str(exc_info.value)
    assert "joinquant" in message
    assert "510300" in message
    assert "20260617" in message
    assert "20260618" in message
    assert "timeout" in message


def test_joinquant_provider_retries_temporary_source_failure() -> None:
    jq = FlakyJoinQuantModule(
        failures_before_success=2,
        response=_prices_frame(["2026-06-18"]),
    )
    provider = JoinQuantMarketDataProvider(jq)

    prices = provider.get_etf_daily_prices(
        "510300",
        start_date=date(2026, 6, 17),
        end_date=date(2026, 6, 18),
    )

    assert len(prices) == 1
    assert len(jq.calls) == 3


def test_joinquant_provider_raises_provider_error_after_retries_exhausted() -> None:
    provider = JoinQuantMarketDataProvider(FailingJoinQuantModule(RuntimeError("timeout")))

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices(
            "510300",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    assert "timeout" in str(exc_info.value)


def test_joinquant_provider_does_not_retry_invalid_returned_rows() -> None:
    jq = FakeJoinQuantModule(_prices_frame(["2026-06-18"], open=["not-a-number"]))
    provider = JoinQuantMarketDataProvider(jq)

    with pytest.raises(MarketDataProviderError):
        provider.get_etf_daily_prices(
            "510300",
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )

    assert len(jq.calls) == 1


def test_joinquant_provider_wraps_row_parsing_errors_with_context() -> None:
    provider = JoinQuantMarketDataProvider(
        FakeJoinQuantModule(_prices_frame(["2026-06-18"], open=["not-a-number"]))
    )

    with pytest.raises(MarketDataProviderError) as exc_info:
        provider.get_etf_daily_prices("510300", end_date=date(2026, 6, 18))

    message = str(exc_info.value)
    assert "joinquant" in message
    assert "510300" in message
    assert "row_index=0" in message
    assert "column=open" in message


def test_joinquant_provider_rejects_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JQ_USERNAME", "")
    monkeypatch.setenv("JQ_PASSWORD", "")

    fake = FakeJoinQuantModule(_empty_prices())

    with pytest.raises(MarketDataProviderError) as exc_info:
        JoinQuantMarketDataProvider(fake)

    message = str(exc_info.value)
    assert "joinquant" in message
    assert "JQ_USERNAME" in message or "JQ_PASSWORD" in message
    assert fake.auth_calls == []


def test_joinquant_provider_authenticates_at_most_once_per_process() -> None:
    jq = FakeJoinQuantModule(_prices_frame(["2026-06-18"]))
    JoinQuantMarketDataProvider(jq)
    JoinQuantMarketDataProvider(jq)

    assert len(jq.auth_calls) == 1
    assert jq.auth_calls[0] == ("dummy-user", "dummy-pass")


def test_joinquant_provider_wraps_auth_failure_as_provider_error() -> None:
    jq = AuthFailingJoinQuantModule(RuntimeError("未开通权限"))

    with pytest.raises(MarketDataProviderError) as exc_info:
        JoinQuantMarketDataProvider(jq)

    message = str(exc_info.value)
    assert "joinquant" in message
    assert "authentication failed" in message
    assert "未开通权限" in message
    assert jq.auth_calls == [("dummy-user", "dummy-pass")]


def test_joinquant_provider_raises_clear_error_when_jqdatasdk_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_missing(_name: str) -> Any:
        raise ModuleNotFoundError("No module named 'jqdatasdk'")

    monkeypatch.setattr(jq_module, "import_module", _raise_missing)

    with pytest.raises(MarketDataProviderError) as exc_info:
        JoinQuantMarketDataProvider()

    message = str(exc_info.value)
    assert "joinquant" in message
    assert "jqdatasdk" in message
    assert "joinquant" in message  # references the extra name


def test_joinquant_provider_name_is_joinquant() -> None:
    assert JoinQuantMarketDataProvider(FakeJoinQuantModule(_empty_prices())).name == "joinquant"


def _prices_frame(
    dates: list[str],
    *,
    open: list[str] | None = None,
    high: list[str] | None = None,
    low: list[str] | None = None,
    close: list[str] | None = None,
    volume: list[int] | None = None,
    factor: list[float] | None = None,
) -> pd.DataFrame:
    n = len(dates)
    return pd.DataFrame(
        {
            "open": open or ["1.230"] * n,
            "high": high or ["1.260"] * n,
            "low": low or ["1.220"] * n,
            "close": close or ["1.250"] * n,
            "volume": volume or [1000] * n,
            "factor": factor or [1.0] * n,
        },
        index=pd.to_datetime(dates),
    )


def _empty_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {"open": [], "high": [], "low": [], "close": [], "volume": [], "factor": []},
        index=pd.to_datetime([]),
    )


class FakeJoinQuantModule:
    def __init__(self, response: pd.DataFrame) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []
        self.auth_calls: list[tuple[str, str]] = []

    def auth(self, username: str, password: str) -> None:
        self.auth_calls.append((username, password))

    def get_price(
        self,
        *,
        security: str,
        start_date: str,
        end_date: str,
        frequency: str,
        skip_paused: bool,
        fq: Any,
        fields: Any,
    ) -> pd.DataFrame:
        self.calls.append(
            {
                "security": security,
                "start_date": start_date,
                "end_date": end_date,
                "frequency": frequency,
                "skip_paused": skip_paused,
                "fq": fq,
                "fields": fields,
            }
        )
        return self.response


class FailingJoinQuantModule(FakeJoinQuantModule):
    def get_price(self, **kwargs: Any) -> pd.DataFrame:  # type: ignore[override]
        self.calls.append({"security": kwargs.get("security")})
        raise RuntimeError("timeout")


class AuthFailingJoinQuantModule(FakeJoinQuantModule):
    def __init__(self, error: Exception) -> None:
        super().__init__(_empty_prices())
        self._error = error

    def auth(self, username: str, password: str) -> None:
        self.auth_calls.append((username, password))
        raise self._error


class FlakyJoinQuantModule(FakeJoinQuantModule):
    def __init__(self, *, failures_before_success: int, response: pd.DataFrame) -> None:
        super().__init__(response)
        self._failures_before_success = failures_before_success

    def get_price(self, **kwargs: Any) -> pd.DataFrame:  # type: ignore[override]
        self.calls.append(
            {
                "security": kwargs.get("security"),
                "start_date": kwargs.get("start_date"),
                "end_date": kwargs.get("end_date"),
            }
        )
        if len(self.calls) <= self._failures_before_success:
            raise RuntimeError("temporary timeout")
        return self.response

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any

from vela_core.market_data_provider import DailyPrice


class MarketDataProviderError(Exception):
    """Raised when a market data provider cannot fetch or normalize data."""


class AkShareMarketDataProvider:
    name = "akshare"

    _required_columns = frozenset({"日期", "开盘", "最高", "最低", "收盘", "成交量"})

    def __init__(self, akshare_module: Any | None = None) -> None:
        self._akshare: Any = (
            akshare_module if akshare_module is not None else import_module("akshare")
        )

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        request_start = _format_date(start_date) if start_date is not None else "20000101"
        request_end = _format_date(end_date) if end_date is not None else _format_date(date.today())

        try:
            rows = self._akshare.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                start_date=request_start,
                end_date=request_end,
                adjust="",
            )
        except Exception as exc:
            raise MarketDataProviderError(
                _error_message(symbol, request_start, request_end, f"AkShare fetch failed: {exc}")
            ) from exc

        try:
            return self._normalize_rows(rows, symbol, request_start, request_end)
        except MarketDataProviderError:
            raise
        except Exception as exc:
            raise MarketDataProviderError(
                _error_message(
                    symbol,
                    request_start,
                    request_end,
                    f"AkShare normalization failed: {exc}",
                )
            ) from exc

    def _normalize_rows(
        self,
        rows: Any,
        symbol: str,
        request_start: str,
        request_end: str,
    ) -> Sequence[DailyPrice]:
        missing_columns = self._required_columns - set(rows.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise MarketDataProviderError(
                _error_message(
                    symbol,
                    request_start,
                    request_end,
                    f"AkShare result missing required columns: {missing}",
                )
            )

        prices = [
            DailyPrice(
                symbol=symbol,
                trade_date=_parse_trade_date(row["日期"]),
                open_price=_parse_decimal(row["开盘"]),
                high_price=_parse_decimal(row["最高"]),
                low_price=_parse_decimal(row["最低"]),
                close_price=_parse_decimal(row["收盘"]),
                adjusted_close=None,
                volume=_parse_volume(row["成交量"]),
            )
            for _, row in rows.iterrows()
        ]
        return sorted(prices, key=lambda price: price.trade_date)


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _parse_trade_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _parse_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _parse_volume(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _error_message(symbol: str, start_date: str, end_date: str, detail: str) -> str:
    return (
        "akshare market data provider error "
        f"symbol={symbol} start_date={start_date} end_date={end_date}: {detail}"
    )

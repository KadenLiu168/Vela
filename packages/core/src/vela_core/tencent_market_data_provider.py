from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from importlib import import_module
from typing import Any

from tenacity import retry, stop_after_attempt, wait_fixed

from vela_core.akshare_market_data_provider import MarketDataProviderError
from vela_core.market_data_provider import DailyPrice

_TENCENT_FETCH_ATTEMPTS = 3
_TENCENT_FETCH_WAIT_SECONDS = 1


class TencentMarketDataProvider:
    name = "tencent"

    _required_columns = frozenset({"date", "open", "close", "high", "low"})

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
        tx_symbol = _to_tx_symbol(symbol)
        request_start = _format_date(start_date) if start_date is not None else "20000101"
        request_end = _format_date(end_date) if end_date is not None else _format_date(date.today())

        try:
            rows = self._fetch_rows(tx_symbol, request_start, request_end)
        except Exception as exc:
            raise MarketDataProviderError(
                _error_message(
                    symbol,
                    request_start,
                    request_end,
                    f"Tencent fetch failed: {exc}",
                )
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
                    f"Tencent normalization failed: {exc}",
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
                    f"Tencent result missing required columns: {missing}",
                )
            )

        prices: list[DailyPrice] = []
        for row_index, row in rows.iterrows():
            trade_date = _parse_trade_date(
                row["date"],
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
                column="date",
            )
            open_price = _parse_price(
                row["open"],
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
                column="open",
            )
            high_price = _parse_price(
                row["high"],
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
                column="high",
            )
            low_price = _parse_price(
                row["low"],
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
                column="low",
            )
            close_price = _parse_price(
                row["close"],
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
                column="close",
            )
            _validate_ohlc(
                open_price,
                high_price,
                low_price,
                close_price,
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
            )

            prices.append(
                DailyPrice(
                    symbol=symbol,
                    trade_date=trade_date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    adjusted_close=None,
                    volume=None,
                )
            )

        return prices

    @retry(
        stop=stop_after_attempt(_TENCENT_FETCH_ATTEMPTS),
        wait=wait_fixed(_TENCENT_FETCH_WAIT_SECONDS),
        reraise=True,
    )
    def _fetch_rows(self, tx_symbol: str, request_start: str, request_end: str) -> Any:
        return self._akshare.stock_zh_a_hist_tx(
            symbol=tx_symbol,
            start_date=request_start,
            end_date=request_end,
            adjust="",
        )


def _to_tx_symbol(symbol: str) -> str:
    """Map a bare 6-digit ETF symbol to Tencent's sh/sz-prefixed form.

    Symbols starting with `15` (Shenzhen ETF segment, e.g. `159915`) get `sz`,
    all other symbols (Shanghai ETF segments, e.g. `510300`, `511010`,
    `512100`, `513500`, `518880`) get `sh`.
    """
    if symbol.startswith("15"):
        return f"sz{symbol}"
    return f"sh{symbol}"


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _parse_trade_date(
    value: Any,
    *,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> date:
    _require_value(
        value,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    try:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="invalid trade date",
        ) from exc


def _parse_price(
    value: Any,
    *,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> Decimal:
    decimal_value = _parse_decimal(
        value,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    if decimal_value <= 0:
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="price must be greater than zero",
        )
    return decimal_value


def _parse_decimal(
    value: Any,
    *,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> Decimal:
    _require_value(
        value,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    if isinstance(value, datetime):
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="invalid decimal",
        )
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="invalid decimal",
        ) from exc
    if not decimal_value.is_finite():
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="decimal must be finite",
        )
    return decimal_value


def _validate_ohlc(
    open_price: Decimal,
    high_price: Decimal,
    low_price: Decimal,
    close_price: Decimal,
    *,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
) -> None:
    if high_price < max(open_price, low_price, close_price):
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column="ohlc",
            value=f"open={open_price} high={high_price} low={low_price} close={close_price}",
            reason="high must be at least open, low, and close",
        )
    if low_price > min(open_price, high_price, close_price):
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column="ohlc",
            value=f"open={open_price} high={high_price} low={low_price} close={close_price}",
            reason="low must be at most open, high, and close",
        )


def _require_value(
    value: Any,
    *,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> None:
    if _is_missing(value):
        raise _validation_error(
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="required value is missing",
        )


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "nat", "<na>"}


def _validation_error(
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    row_index: Any,
    column: str,
    value: Any,
    reason: str,
) -> MarketDataProviderError:
    return MarketDataProviderError(
        _error_message(
            symbol,
            start_date,
            end_date,
            (
                "Tencent row validation failed "
                f"row_index={row_index} column={column} invalid value={value!r} reason={reason}"
            ),
        )
    )


def _error_message(symbol: str, start_date: str, end_date: str, detail: str) -> str:
    return (
        "tencent market data provider error "
        f"symbol={symbol} start_date={start_date} end_date={end_date}: {detail}"
    )

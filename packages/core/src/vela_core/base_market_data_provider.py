from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from importlib import import_module
from typing import Any

import pandas as pd

from vela_core.market_data_provider import DailyPrice, MarketDataProviderError

_FETCH_ATTEMPTS = 3
_FETCH_WAIT_SECONDS = 1


class BaseMarketDataProvider:
    """Shared fetch/normalize/validate engine for ETF daily price providers.

    Subclasses supply provider-specific behavior via a small hook set:
    ``name``, ``_source_label``, ``_column_map``, ``_fetch_rows``,
    ``_format_request_symbol``, and optionally ``_sort_prices``.
    """

    name: str = ""
    _source_label: str = ""
    _column_map: Mapping[str, str] = {}

    def __init__(self, source: Any | None = None) -> None:
        self._source: Any = (
            source if source is not None else import_module("akshare")
        )

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        request_symbol = self._format_request_symbol(symbol)
        request_start = _format_date(start_date) if start_date is not None else "20000101"
        request_end = _format_date(end_date) if end_date is not None else _format_date(date.today())

        try:
            rows = self._fetch_rows(request_symbol, request_start, request_end)
        except Exception as exc:
            raise MarketDataProviderError(
                _error_message(
                    self._source_label,
                    symbol,
                    request_start,
                    request_end,
                    f"{self._source_label} fetch failed: {exc}",
                )
            ) from exc

        try:
            return self._normalize_rows(rows, symbol, request_start, request_end)
        except MarketDataProviderError:
            raise
        except Exception as exc:
            raise MarketDataProviderError(
                _error_message(
                    self._source_label,
                    symbol,
                    request_start,
                    request_end,
                    f"{self._source_label} normalization failed: {exc}",
                )
            ) from exc

    def _normalize_rows(
        self,
        rows: Any,
        symbol: str,
        request_start: str,
        request_end: str,
    ) -> Sequence[DailyPrice]:
        missing_columns = set(self._column_map.values()) - set(rows.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise MarketDataProviderError(
                _error_message(
                    self._source_label,
                    symbol,
                    request_start,
                    request_end,
                    f"{self._source_label} result missing required columns: {missing}",
                )
            )

        prices: list[DailyPrice] = [
            self._extract_row(
                row,
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
            )
            for row_index, row in rows.iterrows()
        ]

        return self._sort_prices(prices)

    def _extract_row(
        self,
        row: Any,
        *,
        symbol: str,
        request_start: str,
        request_end: str,
        row_index: Any,
    ) -> DailyPrice:
        columns = self._column_map
        source_label = self._source_label

        trade_date = _parse_trade_date(
            row[columns["trade_date"]],
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
            column=columns["trade_date"],
        )
        open_price = _parse_price(
            row[columns["open"]],
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
            column=columns["open"],
        )
        high_price = _parse_price(
            row[columns["high"]],
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
            column=columns["high"],
        )
        low_price = _parse_price(
            row[columns["low"]],
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
            column=columns["low"],
        )
        close_price = _parse_price(
            row[columns["close"]],
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
            column=columns["close"],
        )
        _validate_ohlc(
            open_price,
            high_price,
            low_price,
            close_price,
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
        )
        factor = _parse_factor(
            row[columns["factor"]],
            source_label=source_label,
            symbol=symbol,
            request_start=request_start,
            request_end=request_end,
            row_index=row_index,
            column=columns["factor"],
        )
        volume: int | None = None
        if "volume" in columns:
            volume = _parse_volume(
                row[columns["volume"]],
                source_label=source_label,
                symbol=symbol,
                request_start=request_start,
                request_end=request_end,
                row_index=row_index,
                column=columns["volume"],
            )

        return DailyPrice(
            symbol=symbol,
            trade_date=trade_date,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            factor=factor,
            volume=volume,
        )

    def _format_request_symbol(self, symbol: str) -> str:
        return symbol

    def _sort_prices(self, prices: list[DailyPrice]) -> list[DailyPrice]:
        return sorted(prices, key=lambda price: price.trade_date)

    def _fetch_rows(
        self,
        request_symbol: str,
        request_start: str,
        request_end: str,
    ) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement _fetch_rows"
        )


def _format_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _derive_factor_frame(
    unadjusted: Any,
    backward: Any,
    *,
    date_column: str,
    close_column: str,
) -> Any:
    """Merge unadjusted OHLC with backward-adjusted close to derive the factor column.

    Returns ``unadjusted`` with an added ``factor`` column computed as
    ``backward_adjusted_close / unadjusted_close`` per trade date. The
    unadjusted frame is the left/authoritative side so the stored
    ``close_price`` stays the true unadjusted execution price and ``factor``
    is the backward-adjustment (hfq) factor. Dates present in ``unadjusted``
    but missing from ``backward`` yield a null factor and are rejected
    downstream by ``_parse_factor``.
    """
    if close_column not in backward.columns or close_column not in unadjusted.columns:
        # Let _normalize_rows report the missing column uniformly rather than
        # raising a KeyError inside the merge/division below.
        return unadjusted
    backward_close = backward[[date_column, close_column]].rename(
        columns={close_column: "_backward_close"}
    )
    merged = unadjusted.merge(backward_close, on=date_column, how="left")
    backward_numeric = pd.to_numeric(merged["_backward_close"], errors="coerce")
    close_numeric = pd.to_numeric(merged[close_column], errors="coerce")
    merged["factor"] = backward_numeric / close_numeric
    return merged.drop(columns=["_backward_close"])


def _parse_trade_date(
    value: Any,
    *,
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> date:
    _require_value(
        value,
        source_label=source_label,
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
            source_label,
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
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> Decimal:
    decimal_value = _parse_decimal(
        value,
        source_label=source_label,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    if decimal_value <= 0:
        raise _validation_error(
            source_label,
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
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> Decimal:
    _require_value(
        value,
        source_label=source_label,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    if isinstance(value, datetime):
        raise _validation_error(
            source_label,
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
            source_label,
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
            source_label,
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="decimal must be finite",
        )
    return decimal_value


def _parse_factor(
    value: Any,
    *,
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> Decimal:
    decimal_value = _parse_decimal(
        value,
        source_label=source_label,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    if decimal_value <= 0:
        raise _validation_error(
            source_label,
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="factor must be greater than zero",
        )
    return decimal_value


def _parse_volume(
    value: Any,
    *,
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> int:
    decimal_value = _parse_decimal(
        value,
        source_label=source_label,
        symbol=symbol,
        request_start=request_start,
        request_end=request_end,
        row_index=row_index,
        column=column,
    )
    if decimal_value != decimal_value.to_integral_value():
        raise _validation_error(
            source_label,
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="volume must be an integer",
        )
    if decimal_value < 0:
        raise _validation_error(
            source_label,
            symbol,
            request_start,
            request_end,
            row_index=row_index,
            column=column,
            value=value,
            reason="volume must be non-negative",
        )
    return int(decimal_value)


def _validate_ohlc(
    open_price: Decimal,
    high_price: Decimal,
    low_price: Decimal,
    close_price: Decimal,
    *,
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
) -> None:
    if high_price < max(open_price, low_price, close_price):
        raise _validation_error(
            source_label,
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
            source_label,
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
    source_label: str,
    symbol: str,
    request_start: str,
    request_end: str,
    row_index: Any,
    column: str,
) -> None:
    if _is_missing(value):
        raise _validation_error(
            source_label,
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
    source_label: str,
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
            source_label,
            symbol,
            start_date,
            end_date,
            (
                f"{source_label} row validation failed "
                f"row_index={row_index} column={column} invalid value={value!r} reason={reason}"
            ),
        )
    )


def _error_message(
    source_label: str,
    symbol: str,
    start_date: str,
    end_date: str,
    detail: str,
) -> str:
    return (
        f"{source_label} market data provider error "
        f"symbol={symbol} start_date={start_date} end_date={end_date}: {detail}"
    )

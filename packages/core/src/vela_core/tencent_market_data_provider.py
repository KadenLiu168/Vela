from typing import Any

from tenacity import retry, stop_after_attempt, wait_fixed

from vela_core.base_market_data_provider import (
    _FETCH_ATTEMPTS,
    _FETCH_WAIT_SECONDS,
    BaseMarketDataProvider,
    _derive_factor_frame,
)


class TencentMarketDataProvider(BaseMarketDataProvider):
    name = "tencent"
    _source_label = "tencent"

    _column_map = {
        "trade_date": "date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "factor": "factor",
    }

    def _format_request_symbol(self, symbol: str) -> str:
        """Map a bare 6-digit ETF symbol to Tencent's sh/sz-prefixed form.

        Symbols starting with ``15`` (Shenzhen ETF segment, e.g. ``159915``) get
        ``sz``; all other symbols (Shanghai ETF segments, e.g. ``510300``,
        ``511010``, ``512100``, ``513500``, ``518880``) get ``sh``.
        """
        if symbol.startswith("15"):
            return f"sz{symbol}"
        return f"sh{symbol}"

    @retry(
        stop=stop_after_attempt(_FETCH_ATTEMPTS),
        wait=wait_fixed(_FETCH_WAIT_SECONDS),
        reraise=True,
    )
    def _fetch_rows(
        self,
        request_symbol: str,
        request_start: str,
        request_end: str,
    ) -> Any:
        # Stored close_price must stay unadjusted (the execution price), so
        # the unadjusted frame is authoritative; the backward-adjusted (hfq)
        # frame is fetched only to derive the per-row factor.
        unadjusted = self._source.stock_zh_a_hist_tx(
            symbol=request_symbol,
            start_date=request_start,
            end_date=request_end,
            adjust="",
        )
        backward = self._source.stock_zh_a_hist_tx(
            symbol=request_symbol,
            start_date=request_start,
            end_date=request_end,
            adjust="hfq",
        )
        return _derive_factor_frame(
            unadjusted,
            backward,
            date_column="date",
            close_column="close",
        )

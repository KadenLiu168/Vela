from typing import Any

from tenacity import retry, stop_after_attempt, wait_fixed

from vela_core.base_market_data_provider import (
    _FETCH_ATTEMPTS,
    _FETCH_WAIT_SECONDS,
    BaseMarketDataProvider,
    _derive_factor_frame,
)


class AkShareMarketDataProvider(BaseMarketDataProvider):
    name = "akshare"
    _source_label = "akshare"

    _column_map = {
        "trade_date": "日期",
        "open": "开盘",
        "high": "最高",
        "low": "最低",
        "close": "收盘",
        "factor": "factor",
        "volume": "成交量",
    }

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
        unadjusted = self._source.fund_etf_hist_em(
            symbol=request_symbol,
            period="daily",
            start_date=request_start,
            end_date=request_end,
            adjust="",
        )
        backward = self._source.fund_etf_hist_em(
            symbol=request_symbol,
            period="daily",
            start_date=request_start,
            end_date=request_end,
            adjust="hfq",
        )
        return _derive_factor_frame(
            unadjusted,
            backward,
            date_column="日期",
            close_column="收盘",
        )

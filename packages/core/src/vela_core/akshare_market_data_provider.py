from typing import Any

from tenacity import retry, stop_after_attempt, wait_fixed

from vela_core.base_market_data_provider import (
    _FETCH_ATTEMPTS,
    _FETCH_WAIT_SECONDS,
    BaseMarketDataProvider,
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
        return self._source.fund_etf_hist_em(
            symbol=request_symbol,
            period="daily",
            start_date=request_start,
            end_date=request_end,
            adjust="",
        )

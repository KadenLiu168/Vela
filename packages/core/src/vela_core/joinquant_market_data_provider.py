import os
from importlib import import_module
from typing import Any

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

from vela_core.base_market_data_provider import (
    _FETCH_ATTEMPTS,
    _FETCH_WAIT_SECONDS,
    BaseMarketDataProvider,
)
from vela_core.market_data_provider import MarketDataProviderError

_JQ_AUTHENTICATED = False


def _load_joinquant_credentials() -> tuple[str, str]:
    load_dotenv()
    username = os.environ.get("JQ_USERNAME")
    password = os.environ.get("JQ_PASSWORD")
    if not username or not password:
        raise MarketDataProviderError(
            "joinquant market data provider error: "
            "missing JQ_USERNAME or JQ_PASSWORD environment variable; "
            "configure them in a gitignored .env (see .env.example)"
        )
    return username, password


def _format_jq_date(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


class JoinQuantMarketDataProvider(BaseMarketDataProvider):
    name = "joinquant"
    _source_label = "joinquant"

    _column_map = {
        "trade_date": "trade_date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }

    def __init__(self, source: Any | None = None) -> None:
        global _JQ_AUTHENTICATED
        username, password = _load_joinquant_credentials()
        if source is None:
            try:
                source = import_module("jqdatasdk")
            except ModuleNotFoundError as exc:
                raise MarketDataProviderError(
                    "joinquant market data provider error: "
                    "jqdatasdk is not installed; install the 'joinquant' extra "
                    "(e.g. uv pip install -e '.[joinquant]')"
                ) from exc
        if not _JQ_AUTHENTICATED:
            try:
                source.auth(username, password)
            except Exception as exc:
                raise MarketDataProviderError(
                    f"joinquant market data provider error: jqdatasdk authentication failed: {exc}"
                ) from exc
            _JQ_AUTHENTICATED = True
        super().__init__(source)

    def _format_request_symbol(self, symbol: str) -> str:
        if symbol.startswith("15"):
            return f"{symbol}.XSHE"
        return f"{symbol}.XSHG"

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
        rows = self._source.get_price(
            security=request_symbol,
            start_date=_format_jq_date(request_start),
            end_date=_format_jq_date(request_end),
            frequency="daily",
            skip_paused=True,
            fq=None,
            fields=["open", "close", "high", "low", "volume"],
        )
        rows.index.name = "trade_date"
        return rows.reset_index()

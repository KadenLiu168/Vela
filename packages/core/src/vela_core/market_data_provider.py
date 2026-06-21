from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class DailyPrice:
    symbol: str
    trade_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    adjusted_close: Decimal | None = None
    volume: int | None = None


@runtime_checkable
class MarketDataProvider(Protocol):
    name: str

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        ...

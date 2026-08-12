from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

from vela_core.models import ETFInfo, MarketPrice
from vela_core.resolved_session_price import ResolvedSessionPrice


@dataclass(frozen=True)
class GeneratedSignalPosition:
    etf_id: int
    exchange: str
    symbol: str
    target_weight: Decimal
    rank: int | None = None
    score: Decimal | None = None


class StrategyGenerationError(Exception):
    """Expected strategy-specific generation failure."""


class Strategy(Protocol):
    def lookback_days(self) -> int: ...

    def generate_signal(
        self,
        *,
        signal_date: date,
        price_panel: dict[int, list[MarketPrice | ResolvedSessionPrice]],
        active_etfs: list[ETFInfo],
    ) -> list[GeneratedSignalPosition]: ...

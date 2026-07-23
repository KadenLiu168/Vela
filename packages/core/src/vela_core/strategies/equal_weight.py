from datetime import date
from decimal import Decimal

from vela_core.models import ETFInfo, MarketPrice
from vela_core.strategies.types import GeneratedSignalPosition
from vela_core.strategy_config import EqualWeightParams


class EqualWeightStrategy:
    def __init__(self, parameters: EqualWeightParams) -> None:
        self._parameters = parameters

    def lookback_days(self) -> int:
        return 0

    def generate_signal(
        self,
        *,
        signal_date: date,
        price_panel: dict[int, list[MarketPrice]],
        active_etfs: list[ETFInfo],
    ) -> list[GeneratedSignalPosition]:
        del signal_date, price_panel
        target_weight = Decimal("1") / Decimal(len(active_etfs))
        return [
            GeneratedSignalPosition(
                etf_id=etf.id,
                exchange=etf.exchange,
                symbol=etf.symbol,
                target_weight=target_weight,
            )
            for etf in sorted(active_etfs, key=lambda item: item.id)
        ]

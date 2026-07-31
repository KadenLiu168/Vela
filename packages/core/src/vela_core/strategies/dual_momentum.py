from datetime import date

from vela_core.models import ETFInfo, MarketPrice
from vela_core.momentum_scoring import (
    DefensiveFallbackSelection,
    _momentum_score_from_prices,
    rank_momentum_scores,
    select_with_defensive_fallback,
)
from vela_core.strategies.types import GeneratedSignalPosition, StrategyGenerationError
from vela_core.strategy_config import DualMomentumParams
from vela_core.trend_filter import _trend_filter_from_prices


class DualMomentumStrategy:
    def __init__(self, parameters: DualMomentumParams) -> None:
        self._parameters = parameters

    def lookback_days(self) -> int:
        return max(
            self._parameters.momentum.short_window_days,
            self._parameters.momentum.long_window_days,
            self._parameters.trend_filter.moving_average_days,
        )

    def generate_signal(
        self,
        *,
        signal_date: date,
        price_panel: dict[int, list[MarketPrice]],
        active_etfs: list[ETFInfo],
    ) -> list[GeneratedSignalPosition]:
        etfs_by_id = {etf.id: etf for etf in active_etfs}
        defense_lookup = {(etf.exchange, etf.symbol): etf for etf in active_etfs}
        prepared_prices = {
            etf.id: _prices_through(price_panel.get(etf.id, []), signal_date) for etf in active_etfs
        }
        eligible_scores = [
            _momentum_score_from_prices(
                prepared_prices[etf.id],
                etf_id=etf.id,
                as_of_date=signal_date,
                parameters=self._parameters,
            )
            for etf in active_etfs
            if _trend_filter_from_prices(
                prepared_prices[etf.id],
                etf_id=etf.id,
                as_of_date=signal_date,
                parameters=self._parameters,
            ).passes_filter
        ]
        positions: list[GeneratedSignalPosition] = []
        for selection in select_with_defensive_fallback(
            rank_momentum_scores(eligible_scores), self._parameters
        ):
            if isinstance(selection, DefensiveFallbackSelection):
                etf = defense_lookup.get((selection.exchange, selection.symbol))
                if etf is None:
                    raise StrategyGenerationError(
                        "Defensive asset not found as active ETF: "
                        f"{selection.exchange} {selection.symbol}"
                    )
            else:
                etf = etfs_by_id[selection.etf_id]
            positions.append(
                GeneratedSignalPosition(
                    etf_id=etf.id,
                    exchange=etf.exchange,
                    symbol=etf.symbol,
                    target_weight=selection.target_weight,
                    rank=selection.rank,
                    score=selection.score,
                )
            )
        return positions


def _prices_through(prices: list[MarketPrice], signal_date: date) -> list[MarketPrice]:
    return [price for price in prices if price.trade_date <= signal_date]

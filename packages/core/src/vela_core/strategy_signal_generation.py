from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol, TypedDict

from vela_core.models import ETFInfo, MarketPrice
from vela_core.rebalance_dates import generate_rebalance_dates
from vela_core.strategies.registry import resolve_strategy
from vela_core.strategies.types import GeneratedSignalPosition, StrategyGenerationError
from vela_core.strategy_config import StrategyConfig


@dataclass(frozen=True)
class GenerateStrategySignalResult:
    strategy_signal_id: int | None
    signal_date: date
    config_version: str
    status: str
    result: str | None
    error_message: str | None
    positions: list[GeneratedSignalPosition]


class PersistStrategySignalPosition(TypedDict):
    etf_id: int
    rank: int | None
    score: Decimal | None
    target_weight: Decimal


class PersistStrategySignalCallable(Protocol):
    def __call__(
        self,
        *,
        signal_date: date,
        generated_at: datetime,
        status: str,
        result: str | None,
        positions: list[PersistStrategySignalPosition],
        error_message: str | None,
    ) -> int: ...


def generate_strategy_signal(
    *,
    signal_date: date,
    config: StrategyConfig,
    price_panel: dict[int, list[MarketPrice]],
    active_etfs: list[ETFInfo],
    generated_at: datetime | None = None,
    persist: PersistStrategySignalCallable | None = None,
) -> GenerateStrategySignalResult:
    generated_at = generated_at or datetime.now(UTC)
    if not active_etfs:
        return _failed_result(signal_date, config, "No active ETFs found", generated_at, persist)
    try:
        positions = resolve_strategy(config).generate_signal(
            signal_date=signal_date, price_panel=price_panel, active_etfs=active_etfs
        )
    except StrategyGenerationError as exc:
        return _failed_result(signal_date, config, str(exc), generated_at, persist)
    return _success_result(signal_date, config, positions, generated_at, persist)


def generate_historical_strategy_signals(
    *,
    historical_trading_dates: Iterable[date],
    config: StrategyConfig,
    price_panel: dict[int, list[MarketPrice]],
    active_etfs: list[ETFInfo],
    generated_at: datetime | None = None,
    persist: PersistStrategySignalCallable | None = None,
) -> list[GenerateStrategySignalResult]:
    return [
        generate_strategy_signal(
            signal_date=rebalance_date,
            config=config,
            price_panel={
                etf_id: [price for price in prices if price.trade_date <= rebalance_date]
                for etf_id, prices in price_panel.items()
            },
            active_etfs=active_etfs,
            generated_at=generated_at,
            persist=persist,
        )
        for rebalance_date in generate_rebalance_dates(
            historical_trading_dates, frequency=config.rebalance.frequency
        )
    ]


def _success_result(
    signal_date: date,
    config: StrategyConfig,
    positions: list[GeneratedSignalPosition],
    generated_at: datetime,
    persist: PersistStrategySignalCallable | None,
) -> GenerateStrategySignalResult:
    result = "rebalance" if positions else "empty"
    signal_id = (
        None
        if persist is None
        else persist(
            signal_date=signal_date,
            generated_at=generated_at,
            status="success",
            result=result,
            positions=[
                {
                    "etf_id": position.etf_id,
                    "rank": position.rank,
                    "score": position.score,
                    "target_weight": position.target_weight,
                }
                for position in positions
            ],
            error_message=None,
        )
    )
    return GenerateStrategySignalResult(
        strategy_signal_id=signal_id,
        signal_date=signal_date,
        config_version=config.version,
        status="success",
        result=result,
        error_message=None,
        positions=positions,
    )


def _failed_result(
    signal_date: date,
    config: StrategyConfig,
    error_message: str,
    generated_at: datetime,
    persist: PersistStrategySignalCallable | None,
) -> GenerateStrategySignalResult:
    signal_id = (
        None
        if persist is None
        else persist(
            signal_date=signal_date,
            generated_at=generated_at,
            status="failed",
            result=None,
            positions=[],
            error_message=error_message,
        )
    )
    return GenerateStrategySignalResult(
        strategy_signal_id=signal_id,
        signal_date=signal_date,
        config_version=config.version,
        status="failed",
        result=None,
        error_message=error_message,
        positions=[],
    )

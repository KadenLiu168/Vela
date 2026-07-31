import logging
import time
from bisect import bisect_left, bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol, TypedDict

from vela_core.models import ETFInfo, MarketPrice
from vela_core.rebalance_dates import generate_rebalance_dates
from vela_core.strategies.registry import resolve_strategy
from vela_core.strategies.types import GeneratedSignalPosition, Strategy, StrategyGenerationError
from vela_core.strategy_config import StrategyConfig

logger = logging.getLogger(__name__)


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
    return _generate_strategy_signal(
        signal_date=signal_date,
        config=config,
        strategy=resolve_strategy(config),
        price_panel=price_panel,
        active_etfs=active_etfs,
        generated_at=generated_at,
        persist=persist,
    )


def _generate_strategy_signal(
    *,
    signal_date: date,
    config: StrategyConfig,
    strategy: Strategy,
    price_panel: dict[int, list[MarketPrice]],
    active_etfs: list[ETFInfo],
    generated_at: datetime,
    persist: PersistStrategySignalCallable | None,
) -> GenerateStrategySignalResult:
    if not active_etfs:
        return _failed_result(signal_date, config, "No active ETFs found", generated_at, persist)
    try:
        positions = strategy.generate_signal(
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
    started = time.perf_counter()
    trading_dates = list(historical_trading_dates)
    date_range = (
        "none"
        if not trading_dates
        else f"{min(trading_dates).isoformat()}:{max(trading_dates).isoformat()}"
    )
    logger.info(
        "strategy_signal.historical.started strategy_id=%s date_range=%s",
        config.strategy_id,
        date_range,
    )
    rebalance_dates = generate_rebalance_dates(trading_dates, frequency=config.rebalance.frequency)
    if not rebalance_dates:
        logger.info(
            "strategy_signal.historical.completed strategy_id=%s date_range=%s "
            "rebalance_count=0 duration_ms=%.3f",
            config.strategy_id,
            date_range,
            (time.perf_counter() - started) * 1000,
        )
        return []

    strategy = resolve_strategy(config)
    lookback_days = strategy.lookback_days()
    if lookback_days < 0:
        raise ValueError("Strategy lookback_days() must be non-negative")

    etfs_by_id = {etf.id: etf for etf in active_etfs}
    price_dates = {
        etf_id: [price.trade_date for price in prices] for etf_id, prices in price_panel.items()
    }
    for etf_id, dates in price_dates.items():
        if any(previous > current for previous, current in zip(dates, dates[1:], strict=False)):
            raise ValueError(f"Price series for ETF {etf_id} must be ascending by trade_date")

    generated_at = generated_at or datetime.now(UTC)
    results = [
        _generate_strategy_signal(
            signal_date=rebalance_date,
            config=config,
            strategy=strategy,
            price_panel=_historical_price_window(
                rebalance_date=rebalance_date,
                lookback_days=lookback_days,
                price_panel=price_panel,
                price_dates=price_dates,
                etfs_by_id=etfs_by_id,
            ),
            active_etfs=[
                etf
                for etf in active_etfs
                if etf.inception_date is None or etf.inception_date <= rebalance_date
            ],
            generated_at=generated_at,
            persist=persist,
        )
        for rebalance_date in rebalance_dates
    ]
    logger.info(
        "strategy_signal.historical.completed strategy_id=%s date_range=%s "
        "rebalance_count=%s duration_ms=%.3f",
        config.strategy_id,
        date_range,
        len(results),
        (time.perf_counter() - started) * 1000,
    )
    return results


def _historical_price_window(
    *,
    rebalance_date: date,
    lookback_days: int,
    price_panel: dict[int, list[MarketPrice]],
    price_dates: dict[int, list[date]],
    etfs_by_id: dict[int, ETFInfo],
) -> dict[int, list[MarketPrice]]:
    window_size = lookback_days + 1
    windows: dict[int, list[MarketPrice]] = {}
    for etf_id, prices in price_panel.items():
        etf = etfs_by_id.get(etf_id)
        if etf is None or (etf.inception_date is not None and etf.inception_date > rebalance_date):
            continue
        dates = price_dates[etf_id]
        end = bisect_right(dates, rebalance_date)
        inception_start = (
            0 if etf.inception_date is None else bisect_left(dates, etf.inception_date)
        )
        start = max(inception_start, end - window_size)
        windows[etf_id] = prices[start:end]
    return windows


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

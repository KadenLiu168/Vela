from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import ETFInfo
from vela_core.momentum_scoring import (
    DefensiveFallbackSelection,
    TopNSelection,
    calculate_momentum_score,
    rank_momentum_scores,
    select_with_defensive_fallback,
)
from vela_core.rebalance_dates import generate_rebalance_dates
from vela_core.strategy_config import StrategyConfig
from vela_core.strategy_signal_persistence import (
    StrategySignalPositionInput,
    persist_strategy_signal,
)
from vela_core.trend_filter import apply_trend_filter


@dataclass(frozen=True)
class GeneratedSignalPosition:
    etf_id: int
    exchange: str
    symbol: str
    target_weight: Decimal
    rank: int | None = None
    score: Decimal | None = None


@dataclass(frozen=True)
class GenerateStrategySignalResult:
    strategy_signal_id: int
    signal_date: date
    config_version: str
    status: str
    result: str | None
    error_message: str | None
    positions: list[GeneratedSignalPosition]


def generate_strategy_signal(
    session: Session,
    *,
    signal_date: date,
    config: StrategyConfig,
    generated_at: datetime | None = None,
) -> GenerateStrategySignalResult:
    generated_at = generated_at or datetime.now(UTC)
    active_etfs = _list_active_etfs(session)
    if not active_etfs:
        return _persist_failed_signal(
            session,
            signal_date=signal_date,
            config=config,
            generated_at=generated_at,
            error_message="No active ETFs found",
        )

    etfs_by_id = {etf.id: etf for etf in active_etfs}
    eligible_scores = [
        calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=signal_date,
            config=config,
        )
        for etf in active_etfs
        if apply_trend_filter(
            session,
            etf_id=etf.id,
            as_of_date=signal_date,
            config=config,
        ).passes_filter
    ]
    rankings = rank_momentum_scores(eligible_scores)
    selections = select_with_defensive_fallback(rankings, config)

    positions: list[GeneratedSignalPosition] = []
    for selection in selections:
        position = _to_generated_position(session, selection, etfs_by_id)
        if position is None:
            return _persist_failed_signal(
                session,
                signal_date=signal_date,
                config=config,
                generated_at=generated_at,
                error_message=(
                    "Defensive asset not found as active ETF: "
                    f"{config.defense.asset.exchange} {config.defense.asset.symbol}"
                ),
            )
        positions.append(position)

    persistence_result = persist_strategy_signal(
        session,
        signal_date=signal_date,
        config_version=config.version,
        generated_at=generated_at,
        status="success",
        result="rebalance" if positions else "empty",
        positions=[
            StrategySignalPositionInput(
                etf_id=position.etf_id,
                rank=position.rank,
                score=position.score,
                target_weight=position.target_weight,
            )
            for position in positions
        ],
    )

    return GenerateStrategySignalResult(
        strategy_signal_id=persistence_result.strategy_signal.id,
        signal_date=signal_date,
        config_version=config.version,
        status="success",
        result=persistence_result.strategy_signal.result,
        error_message=None,
        positions=positions,
    )


def generate_historical_strategy_signals(
    session: Session,
    *,
    historical_trading_dates: Iterable[date],
    config: StrategyConfig,
    generated_at: datetime | None = None,
) -> list[GenerateStrategySignalResult]:
    rebalance_dates = generate_rebalance_dates(
        historical_trading_dates,
        frequency=config.rebalance.frequency,
    )
    return [
        generate_strategy_signal(
            session,
            signal_date=rebalance_date,
            config=config,
            generated_at=generated_at,
        )
        for rebalance_date in rebalance_dates
    ]


def _list_active_etfs(session: Session) -> list[ETFInfo]:
    return list(
        session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True)).order_by(ETFInfo.id))
    )


def _to_generated_position(
    session: Session,
    selection: TopNSelection | DefensiveFallbackSelection,
    etfs_by_id: dict[int, ETFInfo],
) -> GeneratedSignalPosition | None:
    if isinstance(selection, TopNSelection):
        etf = etfs_by_id[selection.etf_id]
        return GeneratedSignalPosition(
            etf_id=etf.id,
            exchange=etf.exchange,
            symbol=etf.symbol,
            rank=selection.rank,
            score=selection.score,
            target_weight=selection.target_weight,
        )

    defensive_etf = session.scalar(
        select(ETFInfo)
        .where(ETFInfo.exchange == selection.exchange)
        .where(ETFInfo.symbol == selection.symbol)
        .where(ETFInfo.is_active.is_(True))
    )
    if defensive_etf is None:
        return None

    return GeneratedSignalPosition(
        etf_id=defensive_etf.id,
        exchange=defensive_etf.exchange,
        symbol=defensive_etf.symbol,
        rank=selection.rank,
        score=selection.score,
        target_weight=selection.target_weight,
    )


def _persist_failed_signal(
    session: Session,
    *,
    signal_date: date,
    config: StrategyConfig,
    generated_at: datetime,
    error_message: str,
) -> GenerateStrategySignalResult:
    persistence_result = persist_strategy_signal(
        session,
        signal_date=signal_date,
        config_version=config.version,
        generated_at=generated_at,
        status="failed",
        result=None,
        positions=[],
        error_message=error_message,
    )
    return GenerateStrategySignalResult(
        strategy_signal_id=persistence_result.strategy_signal.id,
        signal_date=signal_date,
        config_version=config.version,
        status="failed",
        result=None,
        error_message=error_message,
        positions=[],
    )

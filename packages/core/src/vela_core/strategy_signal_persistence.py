from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import StrategySignal, StrategySignalPosition


@dataclass(frozen=True)
class StrategySignalPositionInput:
    etf_id: int
    target_weight: Decimal
    rank: int | None = None
    score: Decimal | None = None


@dataclass(frozen=True)
class StrategySignalPersistenceResult:
    strategy_signal: StrategySignal
    positions: list[StrategySignalPosition]


def persist_strategy_signal(
    session: Session,
    *,
    strategy_id: str,
    signal_date: date,
    config_version: str,
    generated_at: datetime,
    status: str,
    result: str | None,
    positions: Sequence[StrategySignalPositionInput],
    error_message: str | None = None,
) -> StrategySignalPersistenceResult:
    strategy_signal = StrategySignal(
        signal_date=signal_date,
        strategy_id=strategy_id,
        config_version=config_version,
        generated_at=generated_at,
        status=status,
        result=result,
        error_message=error_message,
    )
    session.add(strategy_signal)
    session.flush()

    signal_positions = [
        StrategySignalPosition(
            strategy_signal_id=strategy_signal.id,
            etf_id=position.etf_id,
            rank=position.rank,
            score=position.score,
            target_weight=position.target_weight,
        )
        for position in positions
    ]
    session.add_all(signal_positions)
    session.flush()

    return StrategySignalPersistenceResult(
        strategy_signal=strategy_signal,
        positions=signal_positions,
    )


def get_latest_successful_strategy_signal(
    session: Session,
    *,
    signal_date: date,
    config_version: str,
) -> StrategySignal | None:
    return session.scalar(
        select(StrategySignal)
        .options(selectinload(StrategySignal.positions))
        .where(StrategySignal.signal_date == signal_date)
        .where(StrategySignal.config_version == config_version)
        .where(StrategySignal.status == "success")
        .order_by(StrategySignal.generated_at.desc(), StrategySignal.id.desc())
        .limit(1)
    )

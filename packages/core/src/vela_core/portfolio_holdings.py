from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import StrategySignal


@dataclass(frozen=True)
class PortfolioHolding:
    etf_id: int
    target_weight: Decimal


@dataclass(frozen=True)
class PortfolioHoldingSnapshot:
    trade_date: date
    signal_date: date | None
    strategy_signal_id: int | None
    holdings: list[PortfolioHolding]


def calculate_portfolio_holdings(
    session: Session,
    *,
    trading_dates: Iterable[date],
    strategy_id: str,
    config_version: str,
) -> list[PortfolioHoldingSnapshot]:
    requested_dates = list(trading_dates)
    if not requested_dates:
        return []

    signals_by_date = _latest_successful_signals_by_date(
        session,
        strategy_id=strategy_id,
        config_version=config_version,
        through_date=max(requested_dates),
    )
    signal_dates = sorted(signals_by_date)
    next_signal_index = 0
    current_signal: StrategySignal | None = None

    snapshots: list[PortfolioHoldingSnapshot] = []
    for trade_date in requested_dates:
        # T+1 effectiveness: a signal dated T uses data through T's close, so it
        # cannot apply on trade_date T itself (look-ahead bias). `signal_date < T`
        # applies it from T+1. The query bound `signal_date <= through_date`
        # (= max(trade_dates)) still fetches every T+1-effective signal.
        while (
            next_signal_index < len(signal_dates) and signal_dates[next_signal_index] < trade_date
        ):
            current_signal = signals_by_date[signal_dates[next_signal_index]]
            next_signal_index += 1

        snapshots.append(_to_snapshot(trade_date, current_signal))

    return snapshots


def _latest_successful_signals_by_date(
    session: Session,
    *,
    strategy_id: str,
    config_version: str,
    through_date: date,
) -> dict[date, StrategySignal]:
    signals = session.scalars(
        select(StrategySignal)
        .options(selectinload(StrategySignal.positions))
        .where(StrategySignal.strategy_id == strategy_id)
        .where(StrategySignal.config_version == config_version)
        .where(StrategySignal.status == "success")
        .where(StrategySignal.signal_date <= through_date)
        .order_by(
            StrategySignal.signal_date.asc(),
            StrategySignal.generated_at.desc(),
            StrategySignal.id.desc(),
        )
    ).all()

    latest_by_date: dict[date, StrategySignal] = {}
    for signal in signals:
        latest_by_date.setdefault(signal.signal_date, signal)

    return latest_by_date


def _to_snapshot(
    trade_date: date,
    signal: StrategySignal | None,
) -> PortfolioHoldingSnapshot:
    if signal is None:
        return PortfolioHoldingSnapshot(
            trade_date=trade_date,
            signal_date=None,
            strategy_signal_id=None,
            holdings=[],
        )

    return PortfolioHoldingSnapshot(
        trade_date=trade_date,
        signal_date=signal.signal_date,
        strategy_signal_id=signal.id,
        holdings=[
            PortfolioHolding(
                etf_id=position.etf_id,
                target_weight=position.target_weight,
            )
            for position in signal.positions
        ],
    )

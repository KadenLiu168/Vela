from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import ETFInfo, StrategySignal, StrategySignalPosition


class LatestStrategySignalReportNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class StrategySignalReportPosition:
    exchange: str
    symbol: str
    target_weight: Decimal
    rank: int | None
    score: Decimal | None
    is_fallback: bool


@dataclass(frozen=True)
class StrategySignalReport:
    signal_id: int
    signal_date: date
    strategy_id: str
    config_version: str
    generated_at: str
    result: str | None
    is_fallback: bool
    positions: list[StrategySignalReportPosition]


def export_latest_strategy_signal_report(
    session: Session,
    *,
    config_version: str,
    signal_date: date | None = None,
) -> str:
    report = get_latest_strategy_signal_report(
        session,
        config_version=config_version,
        signal_date=signal_date,
    )
    if report is None:
        raise LatestStrategySignalReportNotFoundError("No latest successful strategy signal found")

    return _format_report(report)


def get_latest_strategy_signal_report(
    session: Session,
    *,
    config_version: str,
    signal_date: date | None = None,
) -> StrategySignalReport | None:
    signal = _get_latest_successful_signal(
        session,
        config_version=config_version,
        signal_date=signal_date,
    )
    if signal is None:
        return None

    return _to_report(session, signal)


@dataclass(frozen=True)
class StrategySignalListEntry:
    signal_id: int
    signal_date: date
    config_version: str
    result: str | None
    generated_at: str
    is_fallback: bool
    position_count: int


def list_strategy_signals(
    session: Session,
    *,
    strategy_id: str,
    config_version: str,
    limit: int,
    offset: int = 0,
) -> list[StrategySignalListEntry]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    if offset < 0:
        raise ValueError("offset must be non-negative")

    rows = session.execute(
        select(
            StrategySignal.id,
            StrategySignal.signal_date,
            StrategySignal.config_version,
            StrategySignal.result,
            StrategySignal.generated_at,
        )
        .where(StrategySignal.strategy_id == strategy_id)
        .where(StrategySignal.config_version == config_version)
        .where(StrategySignal.status == "success")
        .order_by(StrategySignal.generated_at.desc(), StrategySignal.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    if not rows:
        return []

    ids = [row.id for row in rows]
    counts = dict(
        session.execute(
            select(StrategySignalPosition.strategy_signal_id, func.count(StrategySignalPosition.id))
            .where(StrategySignalPosition.strategy_signal_id.in_(ids))
            .group_by(StrategySignalPosition.strategy_signal_id)
        ).all()
    )
    signals = {
        signal.id: signal
        for signal in session.scalars(
            select(StrategySignal)
            .options(selectinload(StrategySignal.positions))
            .where(StrategySignal.id.in_(ids))
        )
    }

    return [
        StrategySignalListEntry(
            signal_id=row.id,
            signal_date=row.signal_date,
            config_version=row.config_version,
            result=row.result,
            generated_at=row.generated_at.isoformat(),
            is_fallback=_is_fallback_signal(signals[row.id]),
            position_count=counts.get(row.id, 0),
        )
        for row in rows
    ]


def get_strategy_signal_report(
    session: Session,
    *,
    signal_id: int,
) -> StrategySignalReport | None:
    signal = session.scalar(
        select(StrategySignal)
        .options(selectinload(StrategySignal.positions))
        .where(StrategySignal.id == signal_id)
    )
    if signal is None:
        return None

    return _to_report(session, signal)


def _is_fallback_signal(signal: StrategySignal) -> bool:
    return any(
        position.rank is None and position.score is None for position in signal.positions
    )


def _get_latest_successful_signal(
    session: Session,
    *,
    config_version: str,
    signal_date: date | None,
) -> StrategySignal | None:
    statement = (
        select(StrategySignal)
        .options(selectinload(StrategySignal.positions))
        .where(StrategySignal.config_version == config_version)
        .where(StrategySignal.status == "success")
        .order_by(
            StrategySignal.generated_at.desc(),
            StrategySignal.id.desc(),
        )
        .limit(1)
    )
    if signal_date is not None:
        statement = statement.where(StrategySignal.signal_date == signal_date)
    return session.scalar(statement)


def _to_report(session: Session, signal: StrategySignal) -> StrategySignalReport:
    etfs_by_id = {}
    if signal.positions:
        etfs_by_id = {
            etf.id: etf
            for etf in session.scalars(
                select(ETFInfo).where(
                    ETFInfo.id.in_(position.etf_id for position in signal.positions)
                )
            )
        }
    positions = [
        StrategySignalReportPosition(
            exchange=etfs_by_id[position.etf_id].exchange,
            symbol=etfs_by_id[position.etf_id].symbol,
            target_weight=position.target_weight,
            rank=position.rank,
            score=position.score,
            is_fallback=position.rank is None and position.score is None,
        )
        for position in sorted(
            signal.positions,
            key=lambda item: (
                item.rank is None,
                item.rank or 0,
                etfs_by_id[item.etf_id].exchange,
                etfs_by_id[item.etf_id].symbol,
            ),
        )
    ]
    return StrategySignalReport(
        signal_id=signal.id,
        signal_date=signal.signal_date,
        strategy_id=signal.strategy_id,
        config_version=signal.config_version,
        generated_at=signal.generated_at.isoformat(),
        result=signal.result,
        is_fallback=any(position.is_fallback for position in positions),
        positions=positions,
    )


def _format_report(report: StrategySignalReport) -> str:
    lines = [
        "Strategy Signal Report",
        f"Signal date: {report.signal_date.isoformat()}",
        f"Config version: {report.config_version}",
        f"Signal id: {report.signal_id}",
        f"Generated at: {report.generated_at}",
        f"Result: {report.result}",
        f"Fallback: {_yes_no(report.is_fallback)}",
        "Positions:",
    ]
    if not report.positions:
        lines.append("- none")
    else:
        lines.extend(_format_position(position) for position in report.positions)
    return "\n".join(lines) + "\n"


def _format_position(position: StrategySignalReportPosition) -> str:
    rank = "N/A" if position.rank is None else str(position.rank)
    score = "N/A" if position.score is None else str(position.score)
    return (
        f"- {position.exchange} {position.symbol} weight={position.target_weight} "
        f"rank={rank} score={score} fallback={_yes_no(position.is_fallback)}"
    )


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"

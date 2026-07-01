from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import ETFInfo, StrategySignal


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

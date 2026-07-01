from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    LatestStrategySignalReportNotFoundError,
    StrategySignalPositionInput,
    export_latest_strategy_signal_report,
    get_latest_strategy_signal_report,
    persist_strategy_signal,
)
from vela_core.models import Base, ETFInfo


def test_export_latest_strategy_signal_report_formats_positions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            positions=[],
        )
        latest = persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(
                    etf_id=qqq.id,
                    rank=2,
                    score=Decimal("0.700000"),
                    target_weight=Decimal("0.500000"),
                ),
                StrategySignalPositionInput(
                    etf_id=spy.id,
                    rank=1,
                    score=Decimal("0.800000"),
                    target_weight=Decimal("0.500000"),
                ),
            ],
        )
        session.commit()

        report = export_latest_strategy_signal_report(session, config_version="v1")

    assert "Strategy Signal Report" in report
    assert "Signal date: 2026-06-23" in report
    assert "Config version: v1" in report
    assert f"Signal id: {latest.strategy_signal.id}" in report
    assert "Result: rebalance" in report
    assert "Fallback: no" in report
    assert "- NYSEARCA SPY weight=0.500000 rank=1 score=0.800000 fallback=no" in report
    assert "- NYSEARCA QQQ weight=0.500000 rank=2 score=0.700000 fallback=no" in report


def test_export_latest_strategy_signal_report_can_filter_signal_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            positions=[
                StrategySignalPositionInput(
                    etf_id=spy.id,
                    rank=1,
                    score=Decimal("0.600000"),
                    target_weight=Decimal("1.000000"),
                )
            ],
        )
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[],
        )
        session.commit()

        report = export_latest_strategy_signal_report(
            session,
            config_version="v1",
            signal_date=date(2026, 6, 22),
        )

    assert "Signal date: 2026-06-22" in report
    assert "Result: hold" in report


def test_export_latest_strategy_signal_report_marks_fallback() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        defense = _add_etf(session, symbol="SHY")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(
                    etf_id=defense.id,
                    rank=None,
                    score=None,
                    target_weight=Decimal("1.000000"),
                )
            ],
        )
        session.commit()

        report = export_latest_strategy_signal_report(session, config_version="v1")

    assert "Fallback: yes" in report
    assert "- NYSEARCA SHY weight=1.000000 rank=N/A score=N/A fallback=yes" in report


def test_export_latest_strategy_signal_report_raises_when_missing() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(LatestStrategySignalReportNotFoundError):
            export_latest_strategy_signal_report(session, config_version="v1")


def test_get_latest_strategy_signal_report_returns_structured_latest_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            positions=[],
            error_message="missing market data",
        )
        latest = persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 35, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(
                    etf_id=qqq.id,
                    rank=2,
                    score=Decimal("0.700000"),
                    target_weight=Decimal("0.500000"),
                ),
                StrategySignalPositionInput(
                    etf_id=spy.id,
                    rank=1,
                    score=Decimal("0.800000"),
                    target_weight=Decimal("0.500000"),
                ),
            ],
        )
        session.commit()

        report = get_latest_strategy_signal_report(session, config_version="v1")

    assert report is not None
    assert report.signal_id == latest.strategy_signal.id
    assert report.signal_date == date(2026, 6, 23)
    assert report.config_version == "v1"
    assert report.result == "rebalance"
    assert report.is_fallback is False
    assert [position.symbol for position in report.positions] == ["SPY", "QQQ"]


def test_get_latest_strategy_signal_report_returns_none_without_success() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            positions=[],
            error_message="missing market data",
        )
        session.commit()

        report = get_latest_strategy_signal_report(session, config_version="v1")

    assert report is None


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _add_etf(session: Session, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf

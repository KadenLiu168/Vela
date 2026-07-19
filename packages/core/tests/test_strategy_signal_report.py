from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    LatestStrategySignalReportNotFoundError,
    StrategySignalListEntry,
    StrategySignalPositionInput,
    export_latest_strategy_signal_report,
    get_latest_strategy_signal_report,
    get_strategy_signal_report,
    list_strategy_signals,
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
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            source="manual",
            positions=[],
        )
        latest = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
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

        report = export_latest_strategy_signal_report(
            session, strategy_id="Dual_momentum", config_version="v1"
        )

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
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            source="manual",
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
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        session.commit()

        report = export_latest_strategy_signal_report(
            session,
            strategy_id="Dual_momentum",
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
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
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

        report = export_latest_strategy_signal_report(
            session, strategy_id="Dual_momentum", config_version="v1"
        )

    assert "Fallback: yes" in report
    assert "- NYSEARCA SHY weight=1.000000 rank=N/A score=N/A fallback=yes" in report


def test_export_latest_strategy_signal_report_raises_when_missing() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(LatestStrategySignalReportNotFoundError):
            export_latest_strategy_signal_report(
                session, strategy_id="Dual_momentum", config_version="v1"
            )


def test_get_latest_strategy_signal_report_returns_structured_latest_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            source="manual",
            positions=[],
            error_message="missing market data",
        )
        latest = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 35, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
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

        report = get_latest_strategy_signal_report(
            session, strategy_id="Dual_momentum", config_version="v1"
        )

    assert report is not None
    assert report.signal_id == latest.strategy_signal.id
    assert report.signal_date == date(2026, 6, 23)
    assert report.config_version == "v1"
    assert report.result == "rebalance"
    assert report.is_fallback is False
    assert [position.symbol for position in report.positions] == ["SPY", "QQQ"]
    assert [position.name for position in report.positions] == ["SPY ETF", "QQQ ETF"]


def test_get_latest_strategy_signal_report_returns_none_without_success() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            source="manual",
            positions=[],
            error_message="missing market data",
        )
        session.commit()

        report = get_latest_strategy_signal_report(
            session, strategy_id="Dual_momentum", config_version="v1"
        )

    assert report is None


def test_get_latest_strategy_signal_report_scopes_to_exact_strategy_id() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        matching = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        persist_strategy_signal(
            session,
            strategy_id="Other_strategy",
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            source="manual",
            positions=[],
        )
        session.commit()

        report = get_latest_strategy_signal_report(
            session,
            strategy_id="Dual_momentum",
            config_version="v1",
        )
        missing = get_latest_strategy_signal_report(
            session,
            strategy_id="Missing_strategy",
            config_version="v1",
        )

    assert report is not None
    assert report.signal_id == matching.strategy_signal.id
    assert missing is None


def test_list_strategy_signals_returns_successful_signals_ordered_desc() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            source="manual",
            positions=[
                StrategySignalPositionInput(
                    etf_id=spy.id,
                    rank=1,
                    score=Decimal("0.800000"),
                    target_weight=Decimal("1.000000"),
                )
            ],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        session.commit()

        entries = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10
        )

    assert isinstance(entries[0], StrategySignalListEntry)
    assert [entry.signal_date for entry in entries] == [date(2026, 6, 23), date(2026, 6, 22)]
    assert [entry.result for entry in entries] == ["rebalance", "hold"]
    assert entries[1].position_count == 1
    assert entries[1].is_fallback is False


def test_list_strategy_signals_filters_by_strategy_id_and_config_version() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        persist_strategy_signal(
            session,
            strategy_id="Other_strategy",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v2",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        session.commit()

        entries = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10
        )

    assert len(entries) == 1
    assert entries[0].config_version == "v1"


def test_list_strategy_signals_excludes_non_success_status() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 22),
            config_version="v1",
            generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            source="manual",
            positions=[],
            error_message="missing market data",
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        session.commit()

        entries = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10
        )

    assert len(entries) == 1
    assert entries[0].signal_date == date(2026, 6, 23)


def test_list_strategy_signals_paginates_with_limit_and_offset() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        for day in range(5):
            persist_strategy_signal(
                session,
                strategy_id="Dual_momentum",
                signal_date=date(2026, 6, 1 + day),
                config_version="v1",
                generated_at=datetime(2026, 6, 1 + day, 9, 30, tzinfo=UTC),
                status="success",
                result="rebalance",
                source="manual",
                positions=[],
            )
        session.commit()

        page1 = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=2, offset=0
        )
        page2 = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=2, offset=2
        )
        page3 = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=2, offset=4
        )

    assert [entry.signal_date for entry in page1] == [date(2026, 6, 5), date(2026, 6, 4)]
    assert [entry.signal_date for entry in page2] == [date(2026, 6, 3), date(2026, 6, 2)]
    assert [entry.signal_date for entry in page3] == [date(2026, 6, 1)]


def test_list_strategy_signals_returns_empty_when_no_match() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        entries = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10
        )

    assert entries == []


def test_get_strategy_signal_report_returns_report_by_id() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persisted = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(
                    etf_id=spy.id,
                    rank=1,
                    score=Decimal("0.800000"),
                    target_weight=Decimal("1.000000"),
                )
            ],
        )
        session.commit()

        report = get_strategy_signal_report(session, signal_id=persisted.strategy_signal.id)

    assert report is not None
    assert report.signal_id == persisted.strategy_signal.id
    assert report.strategy_id == "Dual_momentum"
    assert report.config_version == "v1"
    assert report.result == "rebalance"
    assert [position.symbol for position in report.positions] == ["SPY"]
    assert [position.name for position in report.positions] == ["SPY ETF"]


def test_get_strategy_signal_report_returns_none_when_missing() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        report = get_strategy_signal_report(session, signal_id=999)

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

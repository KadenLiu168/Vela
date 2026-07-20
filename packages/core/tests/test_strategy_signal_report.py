from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    BacktestSignalSummaryEntry,
    LatestStrategySignalReportNotFoundError,
    StrategySignalListEntry,
    StrategySignalPositionInput,
    export_latest_strategy_signal_report,
    get_latest_strategy_signal_report,
    get_strategy_signal_report,
    list_backtest_signals,
    list_strategy_signals,
    persist_strategy_signal,
)
from vela_core.models import BacktestRun, Base, ETFInfo, StrategySignal


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


def test_list_strategy_signals_filters_by_source_before_pagination() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        _add_signal(session, source="manual", signal_date=date(2026, 6, 1))
        _add_signal(session, source="manual", signal_date=date(2026, 6, 2))
        _add_signal(session, source="manual", signal_date=date(2026, 6, 3))
        _add_signal(session, source="backtest", signal_date=date(2026, 6, 4), run_id=run.id)
        _add_signal(session, source="backtest", signal_date=date(2026, 6, 5), run_id=run.id)
        session.commit()

        manual_all = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10, source="manual"
        )
        manual_page = list_strategy_signals(
            session,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=2,
            offset=0,
            source="manual",
        )
        backtest_all = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10, source="backtest"
        )
        all_signals = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10
        )

    assert [entry.signal_date for entry in manual_all] == [
        date(2026, 6, 3),
        date(2026, 6, 2),
        date(2026, 6, 1),
    ]
    assert [entry.source for entry in manual_all] == ["manual", "manual", "manual"]
    assert len(manual_page) == 2
    assert [entry.signal_date for entry in backtest_all] == [
        date(2026, 6, 5),
        date(2026, 6, 4),
    ]
    assert len(all_signals) == 5


def test_list_strategy_signals_accepts_every_declared_source() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        for source in StrategySignal.SOURCES:
            _add_signal(
                session,
                source=source,
                signal_date=date(2026, 6, 1),
                run_id=run.id if source == "backtest" else None,
            )
        session.commit()

        for source in StrategySignal.SOURCES:
            entries = list_strategy_signals(
                session,
                strategy_id="Dual_momentum",
                config_version="v1",
                limit=10,
                source=source,
            )
            assert len(entries) == 1
            assert entries[0].source == source


def test_list_strategy_signals_omitting_source_returns_all_sources() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        _add_signal(session, source="manual", signal_date=date(2026, 6, 1))
        _add_signal(session, source="scheduled", signal_date=date(2026, 6, 2))
        _add_signal(session, source="backtest", signal_date=date(2026, 6, 3), run_id=run.id)
        _add_signal(session, source="legacy", signal_date=date(2026, 6, 4))
        session.commit()

        entries = list_strategy_signals(
            session, strategy_id="Dual_momentum", config_version="v1", limit=10
        )

    assert sorted(entry.source for entry in entries) == sorted(StrategySignal.SOURCES)


def test_list_backtest_signals_returns_summaries_for_in_scope_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        _add_signal(
            session, source="backtest", signal_date=date(2026, 6, 3), run_id=run.id, result="buy"
        )
        _add_signal(
            session, source="backtest", signal_date=date(2026, 6, 1), run_id=run.id, result="hold"
        )
        _add_signal(
            session,
            source="backtest",
            signal_date=date(2026, 6, 2),
            run_id=run.id,
            result="rebalance",
        )
        session.commit()

        entries = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=10,
        )

    assert entries is not None
    assert all(isinstance(entry, BacktestSignalSummaryEntry) for entry in entries)
    assert [entry.signal_date for entry in entries] == [
        date(2026, 6, 1),
        date(2026, 6, 2),
        date(2026, 6, 3),
    ]
    assert [entry.result for entry in entries] == ["hold", "rebalance", "buy"]
    assert all(entry.backtest_run_id == run.id for entry in entries)


def test_list_backtest_signals_orders_by_signal_date_then_id() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        first_same_day = _add_signal(
            session, source="backtest", signal_date=date(2026, 6, 2), run_id=run.id
        )
        earlier = _add_signal(
            session, source="backtest", signal_date=date(2026, 6, 1), run_id=run.id
        )
        second_same_day = _add_signal(
            session, source="backtest", signal_date=date(2026, 6, 2), run_id=run.id
        )
        session.commit()

        entries = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=10,
        )
        expected_signal_ids = [earlier.id, first_same_day.id, second_same_day.id]

    assert entries is not None
    assert [entry.signal_id for entry in entries] == expected_signal_ids


def test_list_backtest_signals_returns_none_for_foreign_strategy() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        _add_signal(session, source="backtest", signal_date=date(2026, 6, 1), run_id=run.id)
        session.commit()

        entries = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Other_strategy",
            config_version="v1",
            limit=10,
        )

    assert entries is None


def test_list_backtest_signals_returns_none_for_foreign_config() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        _add_signal(session, source="backtest", signal_date=date(2026, 6, 1), run_id=run.id)
        session.commit()

        entries = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v2",
            limit=10,
        )

    assert entries is None


def test_list_backtest_signals_returns_none_for_unknown_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        entries = list_backtest_signals(
            session,
            run_id=999,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=10,
        )

    assert entries is None


def test_list_backtest_signals_returns_empty_when_run_has_no_signals() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        session.commit()

        entries = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=10,
        )

    assert entries == []


def test_list_backtest_signals_paginates_with_limit_and_offset() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        signals = [
            _add_signal(
                session, source="backtest", signal_date=date(2026, 6, 1 + day), run_id=run.id
            )
            for day in range(5)
        ]
        session.commit()

        page1 = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=2,
            offset=0,
        )
        page2 = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=2,
            offset=2,
        )
        page3 = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=2,
            offset=4,
        )
        signal_ids = [signal.id for signal in signals]

    assert [entry.signal_id for entry in page1] == signal_ids[0:2]
    assert [entry.signal_id for entry in page2] == signal_ids[2:4]
    assert [entry.signal_id for entry in page3] == signal_ids[4:5]


def test_list_backtest_signals_does_not_filter_by_status() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        _add_signal(
            session,
            source="backtest",
            signal_date=date(2026, 6, 1),
            run_id=run.id,
            status="failed",
            result=None,
            error_message="missing market data",
        )
        _add_signal(session, source="backtest", signal_date=date(2026, 6, 2), run_id=run.id)
        session.commit()

        entries = list_backtest_signals(
            session,
            run_id=run.id,
            strategy_id="Dual_momentum",
            config_version="v1",
            limit=10,
        )

    assert entries is not None
    assert len(entries) == 2


def test_list_backtest_signals_rejects_invalid_limit() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        session.commit()

        with pytest.raises(ValueError):
            list_backtest_signals(
                session,
                run_id=run.id,
                strategy_id="Dual_momentum",
                config_version="v1",
                limit=0,
            )


def test_list_backtest_signals_rejects_invalid_offset() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        session.commit()

        with pytest.raises(ValueError):
            list_backtest_signals(
                session,
                run_id=run.id,
                strategy_id="Dual_momentum",
                config_version="v1",
                limit=10,
                offset=-1,
            )


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


def _add_backtest_run(session: Session) -> BacktestRun:
    run = BacktestRun(
        strategy_id="Dual_momentum",
        config_version="v1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        parameters_json='{"top_n": 2}',
        started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
        status="success",
        total_return=Decimal("0.120000"),
        annualized_return=Decimal("0.180000"),
        max_drawdown=Decimal("-0.050000"),
        volatility=Decimal("0.200000"),
        sharpe_ratio=Decimal("1.100000"),
    )
    session.add(run)
    session.flush()
    return run


def _add_signal(
    session: Session,
    *,
    source: str,
    signal_date: date,
    run_id: int | None = None,
    result: str | None = "rebalance",
    status: str = "success",
    error_message: str | None = None,
) -> StrategySignal:
    signal = StrategySignal(
        signal_date=signal_date,
        strategy_id="Dual_momentum",
        config_version="v1",
        source=source,
        backtest_run_id=run_id,
        generated_at=datetime(
            signal_date.year, signal_date.month, signal_date.day, 9, 30, tzinfo=UTC
        ),
        status=status,
        result=result,
        error_message=error_message,
        positions=[],
    )
    session.add(signal)
    session.flush()
    return signal

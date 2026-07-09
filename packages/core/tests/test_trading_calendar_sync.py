import sys
from datetime import date, datetime
from types import ModuleType

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from vela_core import sync_trading_calendar_to_db
from vela_core.models import Base, TradingCalendar


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _install_fake_akshare(monkeypatch, trade_dates, *, raise_exc=None) -> None:
    fake = ModuleType("akshare")

    def tool_trade_date_hist_sina():
        if raise_exc is not None:
            raise raise_exc
        return pd.DataFrame({"trade_date": trade_dates})

    fake.tool_trade_date_hist_sina = tool_trade_date_hist_sina
    monkeypatch.setitem(sys.modules, "akshare", fake)


def test_sync_trading_calendar_upserts_trading_days(monkeypatch) -> None:
    _install_fake_akshare(monkeypatch, [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)])
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = sync_trading_calendar_to_db(session)
        session.commit()
        rows = session.query(TradingCalendar).order_by(TradingCalendar.trade_date).all()

    assert result.status == "success"
    assert result.synced_count == 3
    assert result.inserted_count == 3
    assert result.updated_count == 0
    assert result.error_message is None
    assert [row.trade_date for row in rows] == [
        date(2026, 7, 1),
        date(2026, 7, 2),
        date(2026, 7, 3),
    ]
    assert all(row.source == "akshare" for row in rows)


def test_sync_trading_calendar_is_idempotent(monkeypatch) -> None:
    _install_fake_akshare(monkeypatch, [date(2026, 7, 1), date(2026, 7, 2)])
    session_factory = _create_session_factory()

    with session_factory() as session:
        first = sync_trading_calendar_to_db(session)
        session.commit()

    with session_factory() as session:
        second = sync_trading_calendar_to_db(session)
        session.commit()
        rows = session.query(TradingCalendar).all()

    assert first.inserted_count == 2
    assert first.updated_count == 0
    assert second.status == "success"
    assert second.inserted_count == 0
    assert second.updated_count == 2
    assert len(rows) == 2


def test_sync_trading_calendar_failure_returns_failed_status(monkeypatch) -> None:
    _install_fake_akshare(monkeypatch, [], raise_exc=RuntimeError("network down"))
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = sync_trading_calendar_to_db(session)

    assert result.status == "failed"
    assert result.synced_count == 0
    assert result.inserted_count == 0
    assert result.updated_count == 0
    assert "network down" in (result.error_message or "")


def test_sync_trading_calendar_parses_datetime_values(monkeypatch) -> None:
    _install_fake_akshare(
        monkeypatch,
        [datetime(2026, 7, 1, 9, 30), datetime(2026, 7, 2, 15, 0)],
    )
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = sync_trading_calendar_to_db(session)
        session.commit()
        rows = session.query(TradingCalendar).order_by(TradingCalendar.trade_date).all()

    assert result.status == "success"
    assert [row.trade_date for row in rows] == [date(2026, 7, 1), date(2026, 7, 2)]


def test_trading_calendar_model_primary_key_and_fields() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("trading_calendar")}
    pk = inspector.get_pk_constraint("trading_calendar")["constrained_columns"]

    assert {"trade_date", "source", "created_at", "updated_at"} <= columns
    assert pk == ["trade_date"]

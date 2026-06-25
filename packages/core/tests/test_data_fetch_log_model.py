from datetime import UTC, date, datetime
from typing import cast

from sqlalchemy import Table, Text, create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core.models import Base, DataFetchLog


def test_data_fetch_log_table_has_required_columns() -> None:
    table = cast(Table, DataFetchLog.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "source",
        "target_type",
        "fetch_mode",
        "range_start",
        "range_end",
        "requested_symbols",
        "started_at",
        "finished_at",
        "status",
        "rows_fetched",
        "rows_inserted",
        "rows_updated",
        "error_message",
        "created_at",
        "updated_at",
    } <= columns


def test_data_fetch_log_optional_fields_are_nullable() -> None:
    table = cast(Table, DataFetchLog.__table__)

    for column_name in {
        "range_start",
        "range_end",
        "requested_symbols",
        "finished_at",
        "rows_fetched",
        "rows_inserted",
        "rows_updated",
        "error_message",
    }:
        assert table.columns[column_name].nullable is True


def test_data_fetch_log_uses_sqlite_compatible_text_for_requested_symbols() -> None:
    table = cast(Table, DataFetchLog.__table__)

    assert isinstance(table.columns["requested_symbols"].type, Text)


def test_data_fetch_log_supports_expected_status_values() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _data_fetch_log(status=status, fetch_mode="incremental")
                for status in DataFetchLog.STATUSES
            ]
        )
        session.commit()

        statuses = {log.status for log in session.query(DataFetchLog).all()}

    assert statuses == {"running", "success", "failed", "partial"}


def test_data_fetch_log_records_failed_fetch_error() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            _data_fetch_log(
                status="failed",
                fetch_mode="incremental",
                error_message="provider timeout",
            )
        )
        session.commit()

        log = session.query(DataFetchLog).one()

    assert log.status == "failed"
    assert log.error_message == "provider timeout"


def test_data_fetch_log_records_partial_fetch_result() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            _data_fetch_log(
                status="partial",
                fetch_mode="incremental",
                rows_fetched=10,
                rows_inserted=8,
                rows_updated=2,
                error_message="QQQ missing latest price",
            )
        )
        session.commit()

        log = session.query(DataFetchLog).one()

    assert log.status == "partial"
    assert log.rows_fetched == 10
    assert log.rows_inserted == 8
    assert log.rows_updated == 2
    assert log.error_message == "QQQ missing latest price"


def test_data_fetch_log_records_full_and_incremental_fetch_scope() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _data_fetch_log(
                    status="success",
                    fetch_mode="full",
                    range_start=date(2020, 1, 1),
                    range_end=date(2026, 6, 18),
                    requested_symbols='["SPY", "QQQ"]',
                    rows_fetched=3200,
                    rows_inserted=3200,
                    rows_updated=0,
                ),
                _data_fetch_log(
                    status="success",
                    fetch_mode="incremental",
                    range_start=date(2026, 6, 17),
                    range_end=date(2026, 6, 18),
                    requested_symbols='["SPY", "QQQ"]',
                    rows_fetched=4,
                    rows_inserted=2,
                    rows_updated=2,
                ),
            ]
        )
        session.commit()

        logs = {log.fetch_mode: log for log in session.query(DataFetchLog).all()}

    assert logs["full"].source == "yfinance"
    assert logs["full"].target_type == "market_price"
    assert logs["full"].range_start == date(2020, 1, 1)
    assert logs["full"].range_end == date(2026, 6, 18)
    assert logs["full"].requested_symbols == '["SPY", "QQQ"]'
    assert logs["incremental"].range_start == date(2026, 6, 17)
    assert logs["incremental"].range_end == date(2026, 6, 18)


def test_data_fetch_log_has_lookup_indexes() -> None:
    table = cast(Table, DataFetchLog.__table__)
    indexed_columns = {tuple(column.name for column in index.columns) for index in table.indexes}

    assert ("source", "status", "started_at") in indexed_columns
    assert ("target_type", "fetch_mode", "range_start", "range_end") in indexed_columns


def test_alembic_target_metadata_includes_data_fetch_log_table() -> None:
    import importlib.util
    from pathlib import Path

    env_path = Path(__file__).parents[3] / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)

    assert spec is not None
    assert spec.loader is not None

    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)

    assert "data_fetch_log" in alembic_env.target_metadata.tables


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _data_fetch_log(
    *,
    status: str,
    fetch_mode: str,
    range_start: date | None = date(2026, 6, 17),
    range_end: date | None = date(2026, 6, 18),
    requested_symbols: str | None = '["SPY"]',
    rows_fetched: int | None = None,
    rows_inserted: int | None = None,
    rows_updated: int | None = None,
    error_message: str | None = None,
) -> DataFetchLog:
    return DataFetchLog(
        source="yfinance",
        target_type="market_price",
        fetch_mode=fetch_mode,
        range_start=range_start,
        range_end=range_end,
        requested_symbols=requested_symbols,
        started_at=datetime(2026, 6, 18, 9, 30, tzinfo=UTC),
        finished_at=datetime(2026, 6, 18, 9, 31, tzinfo=UTC),
        status=status,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        error_message=error_message,
    )

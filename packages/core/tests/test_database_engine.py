from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from vela_core.database import create_engine_from_url


def test_sqlite_engine_enables_wal_so_reads_do_not_block_during_writes(
    tmp_path: Path,
) -> None:
    engine = create_engine_from_url(f"sqlite+pysqlite:///{tmp_path / 'wal.db'}")

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar() == 30000
        # synchronous=NORMAL is reported as the integer 1 (FULL is 2).
        assert connection.exec_driver_sql("PRAGMA synchronous").scalar() == 1

    # The walk-forward runner holds an open uncommitted write transaction for
    # the full `complete()` duration. WAL must let a polling reader observe
    # committed rows without blocking on the writer's lock; the default
    # rollback journal would raise "database is locked" here.
    writer = sessionmaker(bind=engine)()
    reader = sessionmaker(bind=engine)()
    writer.execute(text("CREATE TABLE probe (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"))
    writer.execute(text("INSERT INTO probe (value) VALUES ('committed')"))
    writer.commit()
    writer.execute(text("INSERT INTO probe (value) VALUES ('uncommitted')"))
    # Writer now has an open transaction with an uncommitted row; the reader
    # must not block and must see only the previously committed row.
    assert reader.execute(text("SELECT COUNT(*) FROM probe")).scalar_one() == 1
    writer.rollback()
    engine.dispose()

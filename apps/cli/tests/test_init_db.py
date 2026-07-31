from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from vela_cli import main as cli


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_init_db_creates_missing_sqlite_database(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "vela.db"

    exit_code = cli.main(["init-db", "--database-url", _sqlite_url(database_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Initialized database at" in captured.out
    assert str(database_path) in captured.out
    assert captured.err == ""
    assert database_path.exists()

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }

    assert "alembic_version" in tables
    assert "etf_info" in tables
    assert "market_price" in tables
    assert "data_fetch_log" in tables
    assert "strategy_signal" in tables
    assert "strategy_signal_position" in tables
    assert "backtest_run" in tables
    assert "backtest_equity_curve" in tables


def test_init_db_is_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    database_path = tmp_path / "vela.db"
    database_url = _sqlite_url(database_path)

    first_exit_code = cli.main(["init-db", "--database-url", database_url])
    first_output = capsys.readouterr()
    second_exit_code = cli.main(["init-db", "--database-url", database_url])
    second_output = capsys.readouterr()

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert "Initialized database at" in first_output.out
    assert "Initialized database at" in second_output.out
    assert first_output.err == ""
    assert second_output.err == ""

    with sqlite3.connect(database_path) as connection:
        revision_count = connection.execute("SELECT COUNT(*) FROM alembic_version").fetchone()[0]

    assert revision_count == 1


def test_init_db_reports_failure(capsys: pytest.CaptureFixture[str]) -> None:
    database_url = "not-a-valid-url"

    exit_code = cli.main(["init-db", "--database-url", database_url])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to initialize database at not-a-valid-url:" in captured.err


def test_cli_initializes_logging_before_dispatch(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr("vela_cli.main.setup_logging", lambda: events.append("logging"))
    monkeypatch.setattr("vela_cli.main.init_db", lambda _database_url: events.append("init-db"))

    assert cli.main(["init-db", "--database-url", "sqlite:///test.db"]) == 0
    assert events == ["logging", "init-db"]

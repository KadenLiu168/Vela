from pathlib import Path

import pytest
from sqlalchemy import create_engine
from vela_cli import main as cli
from vela_core import ETFSessionStatusSyncResult
from vela_core.models import ETFSessionStatus

REPO_ROOT = Path(__file__).resolve().parents[3]


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def _result() -> ETFSessionStatusSyncResult:
    return ETFSessionStatusSyncResult(
        total_entries=4,
        inserted_count=4,
        updated_count=0,
        unchanged_count=0,
    )


def test_sync_etf_session_status_accepts_explicit_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    status_config = tmp_path / "etf_session_status.yaml"
    called_args: list[tuple[str, Path]] = []

    def fake_sync(database_url: str, *, status_config_path: Path) -> ETFSessionStatusSyncResult:
        called_args.append((database_url, status_config_path))
        return _result()

    monkeypatch.setattr(cli, "sync_etf_session_status", fake_sync)

    exit_code = cli.main(
        [
            "sync-etf-session-status",
            "--database-url",
            database_url,
            "--status-config",
            str(status_config),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert called_args == [(database_url, status_config)]
    assert "ETF session status sync status: success" in captured.out
    assert "Total entries: 4" in captured.out
    assert "Inserted: 4" in captured.out
    assert captured.err == ""


def test_sync_etf_session_status_reports_failure(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_sync(database_url: str, *, status_config_path: Path) -> ETFSessionStatusSyncResult:
        raise RuntimeError("status source unavailable")

    monkeypatch.setattr(cli, "sync_etf_session_status", fake_sync)

    exit_code = cli.main(
        [
            "sync-etf-session-status",
            "--database-url",
            "sqlite+pysqlite:///test.db",
            "--status-config",
            "status.yaml",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to sync ETF session status into sqlite+pysqlite:///test.db" in captured.err
    assert "status source unavailable" in captured.err


def test_sync_etf_session_status_populates_test_owned_database(tmp_path: Path) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")

    assert cli.main(["init-db", "--database-url", database_url]) == 0
    assert cli.main(["sync-etf-pool", "--database-url", database_url]) == 0
    assert (
        cli.main(
            [
                "sync-etf-session-status",
                "--database-url",
                database_url,
                "--status-config",
                str(REPO_ROOT / "config" / "etf_session_status.yaml"),
            ]
        )
        == 0
    )

    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert connection.execute(ETFSessionStatus.__table__.select()).fetchall().__len__() == 4

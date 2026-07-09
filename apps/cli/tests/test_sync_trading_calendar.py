from pathlib import Path

import pytest
from vela_cli import main as cli
from vela_core import TradingCalendarSyncResult


def _result(
    *,
    status: str = "success",
    synced: int = 3,
    inserted: int = 3,
    updated: int = 0,
    error: str | None = None,
) -> TradingCalendarSyncResult:
    return TradingCalendarSyncResult(
        synced_count=synced,
        inserted_count=inserted,
        updated_count=updated,
        status=status,
        error_message=error,
    )


def test_sync_trading_calendar_accepts_database_url(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'vela.db'}"
    called: list[str] = []

    def fake_sync(database_url: str) -> TradingCalendarSyncResult:
        called.append(database_url)
        return _result()

    monkeypatch.setattr(cli, "sync_trading_calendar", fake_sync)

    exit_code = cli.main(["sync-trading-calendar", "--database-url", database_url])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert called == [database_url]
    assert "Trading calendar sync status: success" in captured.out
    assert captured.err == ""


def test_sync_trading_calendar_returns_nonzero_on_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'vela.db'}"
    monkeypatch.setattr(
        cli,
        "sync_trading_calendar",
        lambda database_url: _result(status="failed", error="boom"),
    )

    exit_code = cli.main(["sync-trading-calendar", "--database-url", database_url])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "failed" in captured.out
    assert "boom" in captured.out

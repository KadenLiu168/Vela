from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from vela_cli import main as cli
from vela_core import ETFPoolSyncResult
from vela_core.models import ETFInfo


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_sync_etf_pool_accepts_database_url_and_strategy_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    strategy_config = tmp_path / "strategy.yaml"
    called_args: list[tuple[str, Path]] = []

    def fake_sync(database_url: str, *, strategy_config_path: Path) -> ETFPoolSyncResult:
        called_args.append((database_url, strategy_config_path))
        return _result()

    monkeypatch.setattr(cli, "sync_etf_pool", fake_sync)

    exit_code = cli.main(
        [
            "sync-etf-pool",
            "--database-url",
            database_url,
            "--strategy-config",
            str(strategy_config),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert called_args == [(database_url, strategy_config)]
    assert "ETF pool sync status: success" in captured.out
    assert captured.err == ""


def test_sync_etf_pool_uses_default_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    called_args: list[tuple[str, Path]] = []

    def fake_sync(database_url: str, *, strategy_config_path: Path) -> ETFPoolSyncResult:
        called_args.append((database_url, strategy_config_path))
        return _result()

    monkeypatch.setattr(cli, "sync_etf_pool", fake_sync)

    exit_code = cli.main(["sync-etf-pool"])

    assert exit_code == 0
    assert called_args == [
        ("sqlite+pysqlite:///vela.db", Path("/Users/kaden/Vela/config/strategy_v1.yaml"))
    ]


def test_sync_etf_pool_prints_success_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "sync_etf_pool",
        lambda database_url, *, strategy_config_path: _result(),
    )

    exit_code = cli.main(["sync-etf-pool"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ETF pool sync status: success" in captured.out
    assert "Pool: phase1_core" in captured.out
    assert "Total ETFs: 6" in captured.out
    assert "Inserted: 6" in captured.out
    assert "Updated: 0" in captured.out
    assert "Unchanged: 0" in captured.out
    assert captured.err == ""


def test_sync_etf_pool_reports_failure(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_sync(database_url: str, *, strategy_config_path: Path) -> ETFPoolSyncResult:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(cli, "sync_etf_pool", fake_sync)

    exit_code = cli.main(["sync-etf-pool", "--database-url", "sqlite+pysqlite:///bad.db"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to sync ETF pool into sqlite+pysqlite:///bad.db: database unavailable" in (
        captured.err
    )


def test_sync_etf_pool_populates_active_etfs_after_init_db(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")

    assert cli.main(["init-db", "--database-url", database_url]) == 0
    capsys.readouterr()

    exit_code = cli.main(["sync-etf-pool", "--database-url", database_url])

    captured = capsys.readouterr()
    engine = create_engine(database_url)
    with engine.connect() as connection:
        active_count = connection.scalar(
            select(func.count()).select_from(ETFInfo).where(ETFInfo.is_active.is_(True))
        )

    assert exit_code == 0
    assert "ETF pool sync status: success" in captured.out
    assert active_count == 6


def _result() -> ETFPoolSyncResult:
    return ETFPoolSyncResult(
        pool_id="phase1_core",
        total_etfs=6,
        inserted_count=6,
        updated_count=0,
        unchanged_count=0,
    )

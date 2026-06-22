from pathlib import Path

import pytest
from vela_cli import main as cli
from vela_core import MarketDataFetchResult


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_fetch_market_data_accepts_database_url(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    called_database_urls: list[str] = []

    def fake_fetch(database_url: str) -> MarketDataFetchResult:
        called_database_urls.append(database_url)
        return _result(status="success")

    monkeypatch.setattr(cli, "fetch_full_market_data", fake_fetch)

    exit_code = cli.main(["fetch-market-data", "--database-url", database_url])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert called_database_urls == [database_url]
    assert "Market data fetch status: success" in captured.out
    assert captured.err == ""


def test_fetch_market_data_uses_default_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called_database_urls: list[str] = []

    def fake_fetch(database_url: str) -> MarketDataFetchResult:
        called_database_urls.append(database_url)
        return _result(status="success")

    monkeypatch.setattr(cli, "fetch_full_market_data", fake_fetch)

    exit_code = cli.main(["fetch-market-data"])

    assert exit_code == 0
    assert called_database_urls == ["sqlite+pysqlite:///vela.db"]


def test_fetch_market_data_incremental_accepts_database_url(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    called_full_database_urls: list[str] = []
    called_incremental_database_urls: list[str] = []

    def fake_full_fetch(database_url: str) -> MarketDataFetchResult:
        called_full_database_urls.append(database_url)
        return _result(status="success")

    def fake_incremental_fetch(database_url: str) -> MarketDataFetchResult:
        called_incremental_database_urls.append(database_url)
        return _result(status="success")

    monkeypatch.setattr(cli, "fetch_full_market_data", fake_full_fetch)
    monkeypatch.setattr(cli, "fetch_incremental_market_data", fake_incremental_fetch)

    exit_code = cli.main(["fetch-market-data", "--incremental", "--database-url", database_url])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert called_full_database_urls == []
    assert called_incremental_database_urls == [database_url]
    assert "Market data fetch status: success" in captured.out
    assert captured.err == ""


def test_fetch_market_data_incremental_uses_default_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called_database_urls: list[str] = []

    def fake_fetch(database_url: str) -> MarketDataFetchResult:
        called_database_urls.append(database_url)
        return _result(status="success")

    monkeypatch.setattr(cli, "fetch_incremental_market_data", fake_fetch)

    exit_code = cli.main(["fetch-market-data", "--incremental"])

    assert exit_code == 0
    assert called_database_urls == ["sqlite+pysqlite:///vela.db"]


def test_fetch_market_data_without_incremental_uses_full_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called_full_database_urls: list[str] = []
    called_incremental_database_urls: list[str] = []

    def fake_full_fetch(database_url: str) -> MarketDataFetchResult:
        called_full_database_urls.append(database_url)
        return _result(status="success")

    def fake_incremental_fetch(database_url: str) -> MarketDataFetchResult:
        called_incremental_database_urls.append(database_url)
        return _result(status="success")

    monkeypatch.setattr(cli, "fetch_full_market_data", fake_full_fetch)
    monkeypatch.setattr(cli, "fetch_incremental_market_data", fake_incremental_fetch)

    exit_code = cli.main(["fetch-market-data"])

    assert exit_code == 0
    assert called_full_database_urls == ["sqlite+pysqlite:///vela.db"]
    assert called_incremental_database_urls == []


def test_fetch_market_data_prints_success_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "fetch_full_market_data",
        lambda database_url: _result(status="success"),
    )

    exit_code = cli.main(["fetch-market-data"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Market data fetch status: success" in captured.out
    assert "Requested symbols: 2" in captured.out
    assert "Rows fetched: 3" in captured.out
    assert "Rows inserted: 2" in captured.out
    assert "Rows updated: 1" in captured.out
    assert "Failed symbols:" not in captured.out
    assert captured.err == ""


def test_fetch_market_data_prints_partial_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "fetch_full_market_data",
        lambda database_url: _result(
            status="partial",
            failed_symbols=("QQQ",),
            error_message="QQQ: provider failed for QQQ",
        ),
    )

    exit_code = cli.main(["fetch-market-data"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Market data fetch status: partial" in captured.out
    assert "Failed symbols: QQQ" in captured.out
    assert "Error: QQQ: provider failed for QQQ" in captured.out
    assert captured.err == ""


def test_fetch_market_data_prints_failed_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "fetch_full_market_data",
        lambda database_url: _result(
            status="failed",
            requested_symbol_count=0,
            rows_fetched=0,
            rows_inserted=0,
            rows_updated=0,
            error_message="No active ETFs found",
        ),
    )

    exit_code = cli.main(["fetch-market-data"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Market data fetch status: failed" in captured.out
    assert "Error: No active ETFs found" in captured.out
    assert captured.err == ""


def test_fetch_market_data_reports_unhandled_failure(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_fetch(database_url: str) -> MarketDataFetchResult:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(cli, "fetch_full_market_data", fake_fetch)

    exit_code = cli.main(["fetch-market-data", "--database-url", "sqlite+pysqlite:///bad.db"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to fetch market data into sqlite+pysqlite:///bad.db: database unavailable" in (
        captured.err
    )


def _result(
    *,
    status: str,
    requested_symbol_count: int = 2,
    rows_fetched: int = 3,
    rows_inserted: int = 2,
    rows_updated: int = 1,
    failed_symbols: tuple[str, ...] = (),
    error_message: str | None = None,
) -> MarketDataFetchResult:
    return MarketDataFetchResult(
        fetch_log_id=1,
        status=status,
        requested_symbol_count=requested_symbol_count,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        failed_symbols=failed_symbols,
        error_message=error_message,
    )

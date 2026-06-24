from pathlib import Path

import pytest
from vela_cli import main as cli
from vela_core import BacktestReportNotFoundError


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_export_backtest_report_accepts_database_and_run_id(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    calls: list[tuple[str, int]] = []

    def fake_export_backtest_report(database_url: str, *, run_id: int) -> str:
        calls.append((database_url, run_id))
        return "Backtest Report\n"

    monkeypatch.setattr(cli, "export_backtest_report", fake_export_backtest_report)

    exit_code = cli.main(
        ["export-backtest-report", "--database-url", database_url, "--run-id", "42"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [(database_url, 42)]
    assert captured.out == "Backtest Report\n"
    assert captured.err == ""


def test_export_backtest_report_uses_default_database(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_export_backtest_report(database_url: str, *, run_id: int) -> str:
        calls.append((database_url, run_id))
        return "Backtest Report\n"

    monkeypatch.setattr(cli, "export_backtest_report", fake_export_backtest_report)

    exit_code = cli.main(["export-backtest-report", "--run-id", "42"])

    assert exit_code == 0
    assert calls == [("sqlite+pysqlite:///vela.db", 42)]


def test_export_backtest_report_writes_output_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "backtest-report.txt"
    monkeypatch.setattr(
        cli,
        "export_backtest_report",
        lambda database_url, *, run_id: "Backtest Report\n",
    )

    exit_code = cli.main(["export-backtest-report", "--run-id", "42", "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output.read_text() == "Backtest Report\n"
    assert f"Exported backtest report to {output}" in captured.out
    assert captured.err == ""


def test_export_backtest_report_reports_missing_run(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_export_backtest_report(database_url: str, *, run_id: int) -> str:
        raise BacktestReportNotFoundError("Backtest run not found: 42")

    monkeypatch.setattr(cli, "export_backtest_report", fake_export_backtest_report)

    exit_code = cli.main(["export-backtest-report", "--run-id", "42"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to export backtest report: Backtest run not found: 42" in captured.err

from datetime import date
from pathlib import Path

import pytest
from vela_cli import main as cli
from vela_core import LatestStrategySignalReportNotFoundError


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_export_signal_report_accepts_database_config_and_signal_date(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    strategy_config = tmp_path / "strategy.yaml"
    calls: list[tuple[str, Path, date | None]] = []

    def fake_export_signal_report(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
    ) -> str:
        calls.append((database_url, strategy_config_path, signal_date))
        return "Strategy Signal Report\n"

    monkeypatch.setattr(cli, "export_signal_report", fake_export_signal_report)

    exit_code = cli.main(
        [
            "export-signal-report",
            "--database-url",
            database_url,
            "--strategy-config",
            str(strategy_config),
            "--signal-date",
            "2026-06-23",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [(database_url, strategy_config, date(2026, 6, 23))]
    assert captured.out == "Strategy Signal Report\n"
    assert captured.err == ""


def test_export_signal_report_uses_default_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Path, date | None]] = []

    def fake_export_signal_report(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
    ) -> str:
        calls.append((database_url, strategy_config_path, signal_date))
        return "Strategy Signal Report\n"

    monkeypatch.setattr(cli, "export_signal_report", fake_export_signal_report)

    exit_code = cli.main(["export-signal-report"])

    assert exit_code == 0
    assert calls == [
        (
            "sqlite+pysqlite:///vela.db",
            cli.DEFAULT_STRATEGY_CONFIG_PATH,
            None,
        )
    ]


def test_export_signal_report_writes_output_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "signal-report.txt"
    monkeypatch.setattr(
        cli,
        "export_signal_report",
        lambda database_url, *, strategy_config_path, signal_date: "Strategy Signal Report\n",
    )

    exit_code = cli.main(["export-signal-report", "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output.read_text() == "Strategy Signal Report\n"
    assert f"Exported signal report to {output}" in captured.out
    assert captured.err == ""


def test_export_signal_report_reports_missing_latest_signal(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_export_signal_report(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
    ) -> str:
        raise LatestStrategySignalReportNotFoundError("No latest successful strategy signal found")

    monkeypatch.setattr(cli, "export_signal_report", fake_export_signal_report)

    exit_code = cli.main(["export-signal-report"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to export signal report: No latest successful strategy signal found" in (
        captured.err
    )

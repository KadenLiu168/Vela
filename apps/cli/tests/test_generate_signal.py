from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from vela_cli import main as cli
from vela_core import GeneratedSignalPosition, GenerateStrategySignalResult


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_generate_signal_accepts_database_config_and_signal_date(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    strategy_config = tmp_path / "strategy.yaml"
    calls: list[tuple[str, Path, date | None, str]] = []

    def fake_generate_signal(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
        source: str,
    ) -> GenerateStrategySignalResult:
        calls.append((database_url, strategy_config_path, signal_date, source))
        return _result(status="success")

    monkeypatch.setattr(cli, "generate_signal", fake_generate_signal)

    exit_code = cli.main(
        [
            "generate-signal",
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
    assert calls == [(database_url, strategy_config, date(2026, 6, 23), "manual")]
    assert "Strategy signal status: success" in captured.out
    assert captured.err == ""


def test_generate_signal_uses_default_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Path, date | None, str]] = []

    def fake_generate_signal(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
        source: str,
    ) -> GenerateStrategySignalResult:
        calls.append((database_url, strategy_config_path, signal_date, source))
        return _result(status="success")

    monkeypatch.setattr(cli, "generate_signal", fake_generate_signal)

    exit_code = cli.main(["generate-signal"])

    assert exit_code == 0
    assert calls == [
        (
            "sqlite+pysqlite:///vela.db",
            cli.DEFAULT_STRATEGY_CONFIG_PATH,
            None,
            "manual",
        )
    ]


def test_generate_signal_forwards_scheduled_source(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_generate_signal(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
        source: str,
    ) -> GenerateStrategySignalResult:
        calls.append(source)
        return _result(status="success")

    monkeypatch.setattr(cli, "generate_signal", fake_generate_signal)

    assert cli.main(["generate-signal", "--source", "scheduled"]) == 0
    assert calls == ["scheduled"]


@pytest.mark.parametrize("source", ["backtest", "legacy", "unknown"])
def test_generate_signal_rejects_unsupported_source_before_core_call(
    source: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(cli, "generate_signal", lambda *args, **kwargs: calls.append(source))

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["generate-signal", "--source", source])

    assert exc_info.value.code == 2
    assert calls == []


def test_generate_signal_prints_success_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "generate_signal",
        lambda database_url, *, strategy_config_path, signal_date, source: _result(
            status="success"
        ),
    )

    exit_code = cli.main(["generate-signal"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Strategy signal status: success" in captured.out
    assert "Result: rebalance" in captured.out
    assert "Signal date: 2026-06-23" in captured.out
    assert "Config version: v1" in captured.out
    assert "Signal id: 42" in captured.out
    assert "- SSE 510300 weight=0.5 rank=1 score=0.8" in captured.out
    assert captured.err == ""


def test_generate_signal_prints_failed_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "generate_signal",
        lambda database_url, *, strategy_config_path, signal_date, source: _result(
            status="failed",
            result=None,
            positions=[],
            error_message="No active ETFs found",
        ),
    )

    exit_code = cli.main(["generate-signal"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Strategy signal status: failed" in captured.out
    assert "Error: No active ETFs found" in captured.out
    assert captured.err == ""


def test_generate_signal_reports_unhandled_failure(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_generate_signal(
        database_url: str,
        *,
        strategy_config_path: Path,
        signal_date: date | None,
        source: str,
    ) -> GenerateStrategySignalResult:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(cli, "generate_signal", fake_generate_signal)

    exit_code = cli.main(["generate-signal", "--database-url", "sqlite+pysqlite:///bad.db"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to generate signal in sqlite+pysqlite:///bad.db: database unavailable" in (
        captured.err
    )


def _result(
    *,
    status: str,
    result: str | None = "rebalance",
    positions: list[GeneratedSignalPosition] | None = None,
    error_message: str | None = None,
) -> GenerateStrategySignalResult:
    return GenerateStrategySignalResult(
        strategy_signal_id=42,
        signal_date=date(2026, 6, 23),
        config_version="v1",
        status=status,
        result=result,
        error_message=error_message,
        positions=positions
        if positions is not None
        else [
            GeneratedSignalPosition(
                etf_id=1,
                exchange="SSE",
                symbol="510300",
                rank=1,
                score=Decimal("0.8"),
                target_weight=Decimal("0.5"),
            )
        ],
    )

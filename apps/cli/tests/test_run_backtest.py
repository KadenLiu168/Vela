from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from vela_cli import main as cli
from vela_core import BacktestRunResult


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def test_run_backtest_accepts_database_config_and_date_range(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _sqlite_url(tmp_path / "vela.db")
    strategy_config = tmp_path / "strategy.yaml"
    calls: list[tuple[str, Path, date, date]] = []

    def fake_run_backtest(
        database_url: str,
        *,
        strategy_config_path: Path,
        start_date: date,
        end_date: date,
    ) -> BacktestRunResult:
        calls.append((database_url, strategy_config_path, start_date, end_date))
        return _result()

    monkeypatch.setattr(cli, "run_backtest", fake_run_backtest)

    exit_code = cli.main(
        [
            "run-backtest",
            "--database-url",
            database_url,
            "--strategy-config",
            str(strategy_config),
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-01-31",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls == [(database_url, strategy_config, date(2026, 1, 1), date(2026, 1, 31))]
    assert "Backtest run id: 42" in captured.out
    assert captured.err == ""


def test_run_backtest_uses_default_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Path, date, date]] = []

    def fake_run_backtest(
        database_url: str,
        *,
        strategy_config_path: Path,
        start_date: date,
        end_date: date,
    ) -> BacktestRunResult:
        calls.append((database_url, strategy_config_path, start_date, end_date))
        return _result()

    monkeypatch.setattr(cli, "run_backtest", fake_run_backtest)

    exit_code = cli.main(["run-backtest", "--start-date", "2026-01-01", "--end-date", "2026-01-31"])

    assert exit_code == 0
    assert calls == [
        (
            "sqlite+pysqlite:///vela.db",
            cli.DEFAULT_STRATEGY_CONFIG_PATH,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )
    ]


def test_run_backtest_prints_core_metric_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "run_backtest",
        lambda database_url, *, strategy_config_path, start_date, end_date: _result(),
    )

    exit_code = cli.main(["run-backtest", "--start-date", "2026-01-01", "--end-date", "2026-01-31"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Backtest status: success" in captured.out
    assert "Backtest run id: 42" in captured.out
    assert "Date range: 2026-01-01 to 2026-01-31" in captured.out
    assert "Trading days: 21" in captured.out
    assert "Signals generated: 5" in captured.out
    assert "Total return: 0.120000" in captured.out
    assert "Annualized return: 0.180000" in captured.out
    assert "Max drawdown: -0.050000" in captured.out
    assert "Volatility: 0.140000" in captured.out
    assert "Sharpe ratio: 1.100000" in captured.out
    assert captured.err == ""


def test_run_backtest_reports_failure(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_backtest(
        database_url: str,
        *,
        strategy_config_path: Path,
        start_date: date,
        end_date: date,
    ) -> BacktestRunResult:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(cli, "run_backtest", fake_run_backtest)

    exit_code = cli.main(
        [
            "run-backtest",
            "--database-url",
            "sqlite+pysqlite:///bad.db",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-01-31",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Failed to run backtest in sqlite+pysqlite:///bad.db: database unavailable" in (
        captured.err
    )


def _result() -> BacktestRunResult:
    return BacktestRunResult(
        backtest_run_id=42,
        status="success",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        trading_day_count=21,
        signal_count=5,
        total_return=Decimal("0.120000"),
        annualized_return=Decimal("0.180000"),
        max_drawdown=Decimal("-0.050000"),
        sharpe_ratio=Decimal("1.100000"),
        volatility=Decimal("0.140000"),
    )

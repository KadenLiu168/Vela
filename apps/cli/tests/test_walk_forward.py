from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from vela_cli import main as cli
from vela_core.migration import run_alembic_upgrade
from vela_core.models import ETFInfo, MarketPrice, TradingCalendar, WalkForwardRun
from vela_core.walk_forward.report import WalkForwardReport

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_walk_forward_writes_report_to_output(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "report.txt"
    calls: list[tuple[str, Path]] = []

    def fake_run(database_url: str, *, config_path: Path) -> WalkForwardReport:
        calls.append((database_url, config_path))
        return WalkForwardReport()

    monkeypatch.setattr(cli, "run_walk_forward", fake_run)

    assert cli.main(["walk-forward", "--config", "config.yaml", "--output", str(output)]) == 0
    assert calls == [("sqlite+pysqlite:///vela.db", Path("config.yaml"))]
    assert "Walk-forward report" in output.read_text()


def test_walk_forward_prints_persisted_id_after_managed_run(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "run_walk_forward", lambda *_args, **_kwargs: WalkForwardReport(walk_forward_run_id=12)
    )

    assert cli.main(["walk-forward", "--config", "config.yaml"]) == 0

    assert "Walk-forward run id: 12" in capsys.readouterr().out


def test_walk_forward_commit_failure_does_not_print_flushed_id(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "run_walk_forward",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("commit failed")),
    )

    assert cli.main(["walk-forward", "--config", "config.yaml"]) == 1

    assert "Walk-forward run id:" not in capsys.readouterr().out


def test_walk_forward_reports_runtime_failure(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "run_walk_forward",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad config")),
    )

    assert cli.main(["walk-forward", "--config", "missing.yaml"]) == 1
    assert "Failed to run walk-forward" in capsys.readouterr().err


def test_walk_forward_reports_missing_config(capsys) -> None:
    assert cli.main(["walk-forward", "--config", "does-not-exist.yaml"]) == 1
    assert "Failed to read configuration file" in capsys.readouterr().err


def test_walk_forward_success_prints_run_id_and_persists_success_parent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'cli-success.db'}"
    config_path = _write_walk_forward_config(tmp_path)
    run_alembic_upgrade(database_url, REPOSITORY_ROOT / "alembic")
    factory = _seed_market_fixture(database_url)

    exit_code = cli.main(
        ["walk-forward", "--config", str(config_path), "--database-url", database_url]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Walk-forward run id:" in output
    run_id = int(
        [line for line in output.splitlines() if "Walk-forward run id:" in line][0].split(":")[1]
    )
    with factory() as session:
        parent = session.get(WalkForwardRun, run_id)
        assert parent is not None
        assert parent.status == "success"
        assert parent.finished_at is not None
        assert parent.window_count == 3


def test_walk_forward_runtime_failure_leaves_failed_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'cli-failure.db'}"
    config_path = _write_walk_forward_config(tmp_path)
    run_alembic_upgrade(database_url, REPOSITORY_ROOT / "alembic")
    factory = _seed_market_fixture(database_url)

    from vela_core.walk_forward import runner as runner_module

    original_run_backtest = runner_module.run_backtest
    oos_calls = 0

    def fail_first_oos(current_session, **kwargs):
        nonlocal oos_calls
        if kwargs["calculate_benchmarks"]:
            oos_calls += 1
            if oos_calls == 1:
                raise RuntimeError("cli benchmark failure")
        return original_run_backtest(current_session, **kwargs)

    monkeypatch.setattr(runner_module, "run_backtest", fail_first_oos)
    exit_code = cli.main(
        ["walk-forward", "--config", str(config_path), "--database-url", database_url]
    )
    error = capsys.readouterr().err

    assert exit_code == 1
    assert "cli benchmark failure" in error
    with factory() as session:
        parents = session.scalars(select(WalkForwardRun)).all()
        assert len(parents) == 1
        assert parents[0].status == "failed"
        assert "cli benchmark failure" in parents[0].error_message


def test_walk_forward_preflight_failure_leaves_no_parent(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'cli-preflight.db'}"
    run_alembic_upgrade(database_url, REPOSITORY_ROOT / "alembic")
    factory = sessionmaker(bind=create_engine(database_url))
    strategy_path = tmp_path / "strategy.yaml"
    strategy_path.write_text(
        """strategy_id: dual_momentum
version: v1
type: dual_momentum
universe_config: pool.yaml
rebalance: {frequency: weekly}
parameters:
  momentum: {short_window_days: 20, long_window_days: 80}
  score_weights: {short: 0.4, long: 0.6}
  trend_filter: {moving_average_days: 60, price_relation: above}
  selection: {top_n: 1}
  defense: {assets: [{exchange: SSE, symbol: '511010'}]}
costs: {transaction_cost_bps: 10}
performance: {risk_free_rate: 0.02}
"""
    )
    config_path = tmp_path / "walk.yaml"
    config_path.write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2020-01-01, end_date: 2021-12-31,
  train_years: 1, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1]}]
"""
    )

    exit_code = cli.main(
        ["walk-forward", "--config", str(config_path), "--database-url", database_url]
    )

    assert exit_code == 1
    with factory() as session:
        assert session.scalar(select(WalkForwardRun.id)) is None


def test_walk_forward_worker_once_processes_at_most_one_cycle(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    class FakeWorker:
        def __init__(self, database_url: str) -> None:
            calls.append(database_url)

        def run_once(self) -> bool:
            calls.append("once")
            return True

    monkeypatch.setattr(cli, "WalkForwardWorker", FakeWorker)

    assert (
        cli.main(
            [
                "walk-forward-worker",
                "--database-url",
                f"sqlite+pysqlite:///{tmp_path / 'worker.db'}",
                "--once",
            ]
        )
        == 0
    )
    assert calls == [f"sqlite+pysqlite:///{tmp_path / 'worker.db'}", "once"]


def test_walk_forward_worker_reports_non_sqlite_error(capsys, monkeypatch) -> None:
    class FakeWorker:
        def __init__(self, _database_url: str) -> None:
            raise ValueError("walk-forward-worker only supports SQLite database URLs")

    monkeypatch.setattr(cli, "WalkForwardWorker", FakeWorker)

    assert (
        cli.main(
            [
                "walk-forward-worker",
                "--database-url",
                "postgresql+psycopg://user:pass@localhost/vela",
                "--once",
            ]
        )
        == 1
    )
    assert "SQLite" in capsys.readouterr().err


def _write_walk_forward_config(tmp_path: Path) -> Path:
    strategy_path = tmp_path / "strategy.yaml"
    strategy_path.write_text(
        """strategy_id: cli_dual_momentum
version: test-v1
type: dual_momentum
universe_config: pool.yaml
rebalance: {frequency: weekly}
parameters:
  momentum: {short_window_days: 20, long_window_days: 80}
  score_weights: {short: 0.4, long: 0.6}
  trend_filter: {moving_average_days: 60, price_relation: above}
  selection: {top_n: 1}
  defense: {assets: [{exchange: SSE, symbol: '510300'}]}
costs: {transaction_cost_bps: 5}
performance: {risk_free_rate: 0.02}
""",
        encoding="utf-8",
    )
    config_path = tmp_path / "walk-forward.yaml"
    config_path.write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2018-01-02, end_date: 2022-01-10,
  train_years: 1, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1]}]
""",
        encoding="utf-8",
    )
    return config_path


def _seed_market_fixture(database_url: str) -> sessionmaker:
    sessions: list[date] = []
    current = date(2017, 6, 1)
    while current <= date(2022, 1, 10):
        if current.weekday() < 5:
            sessions.append(current)
        current += timedelta(days=1)
    engine = create_engine(database_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        csi_300 = ETFInfo(
            exchange="SSE",
            symbol="510300",
            name="CSI 300 fixture ETF",
            currency="CNY",
            category="risk",
        )
        defensive = ETFInfo(
            exchange="SSE",
            symbol="511010",
            name="Defensive fixture ETF",
            currency="CNY",
            category="defense",
        )
        session.add_all([csi_300, defensive])
        session.flush()
        session.add_all(
            TradingCalendar(trade_date=trade_date, source="cli-walk-forward-test")
            for trade_date in sessions
        )
        session.add_all(
            price
            for index, trade_date in enumerate(sessions)
            for price in (
                _price(csi_300.id, trade_date, index, Decimal("0.040")),
                _price(defensive.id, trade_date, index, Decimal("0.070")),
            )
        )
        session.commit()
    return factory


def _price(etf_id: int, trade_date: date, index: int, step: Decimal) -> MarketPrice:
    close = Decimal("100") + step * index + Decimal(index % 7) * Decimal("0.010")
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close,
        high_price=close,
        low_price=close,
        close_price=close,
        factor_hfq=Decimal("1"),
        volume=1000,
    )

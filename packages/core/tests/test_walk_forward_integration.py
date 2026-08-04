from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from vela_core.database import managed_session
from vela_core.migration import run_alembic_upgrade
from vela_core.models import (
    BacktestBenchmark,
    BacktestBenchmarkEquityCurve,
    BacktestEquityCurve,
    BacktestRun,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    StrategySignalPosition,
    TradingCalendar,
)
from vela_core.walk_forward.config import load_walk_forward_config
from vela_core.walk_forward.runner import WalkForwardRunner

REPOSITORY_ROOT = Path(__file__).parents[3]


def test_real_walk_forward_evidence_contract_uses_alembic_sqlite_fixture(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward.db'}"
    config_path = _write_walk_forward_config(tmp_path)
    run_alembic_upgrade(database_url, REPOSITORY_ROOT / "alembic")
    engine = create_engine(database_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _seed_walk_forward_fixture(factory)

    with managed_session(factory) as session:
        report = WalkForwardRunner(load_walk_forward_config(config_path)).run(session)

    assert len(report.windows) == 3
    assert [item.window.test_start.year for item in report.windows] == [2019, 2020, 2021]
    assert [
        (
            item.oos_total_return,
            item.oos_annualized_return,
            item.oos_sharpe,
            item.oos_max_drawdown,
            item.oos_volatility,
        )
        for item in report.windows
    ] == [
        (0.138485, 0.138891, 34.363878, -0.0005, 0.003077),
        (0.122404, 0.122404, 33.971917, -0.0005, 0.002694),
        (0.106688, 0.107932, 31.442503, -0.0005, 0.002502),
    ]
    assert all(item.oos_version.startswith("wf-") for item in report.windows)
    assert len({item.oos_version for item in report.windows}) == 1
    assert all(
        value is not None
        for item in report.windows
        for value in (
            item.oos_total_return,
            item.oos_annualized_return,
            item.oos_sharpe,
            item.oos_max_drawdown,
            item.oos_volatility,
        )
    )
    aggregate = report.aggregate()
    assert aggregate["total_return"] == {
        "mean": pytest.approx(0.12252566666666667),
        "median": 0.122404,
        "min": 0.106688,
        "max": 0.138485,
        "std": pytest.approx(0.012981355972658974),
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert aggregate["sharpe_ratio"]["mean"] == pytest.approx(33.25943266666667)
    assert aggregate["max_drawdown"]["min"] == -0.0005
    assert aggregate["volatility"]["std"] == pytest.approx(0.0002390206871567582)
    comparisons = report.benchmark_differences()
    assert set(comparisons) == {
        "equal_weight_monthly",
        "csi_300_buy_hold",
    }
    assert report.positive_window_rate() == {
        "numerator": 3,
        "denominator": 3,
        "value": 1.0,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert report.generalization_gap() == {
        "mean": pytest.approx(1.1192676666666668),
        "median": pytest.approx(0.43642799999999937),
        "min": pytest.approx(0.391961000000002),
        "max": pytest.approx(2.529413999999999),
        "std": pytest.approx(0.9972892725056695),
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert comparisons["equal_weight_monthly"]["total_return"]["mean"] == pytest.approx(
        0.019100333333333334
    )
    assert comparisons["equal_weight_monthly"]["total_return"]["min"] == pytest.approx(0.014433)
    assert comparisons["csi_300_buy_hold"]["total_return"]["mean"] == pytest.approx(
        0.04020233333333333
    )
    assert comparisons["csi_300_buy_hold"]["total_return"]["min"] == pytest.approx(0.031364)
    assert comparisons["equal_weight_monthly"]["outperformance_rate"] == {
        "numerator": 3,
        "denominator": 3,
        "value": 1.0,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert comparisons["csi_300_buy_hold"]["outperformance_rate"] == {
        "numerator": 3,
        "denominator": 3,
        "value": 1.0,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert report.parameter_stability()["parameters.selection.top_n"] == {
        "value_frequencies": {"1": 3},
        "transition_count": 0,
        "comparison_count": 2,
        "transition_rate": 0.0,
    }

    with factory() as session:
        runs = session.scalars(select(BacktestRun).order_by(BacktestRun.id)).all()
        assert len(runs) == 3
        assert [(run.start_date, run.end_date) for run in runs] == [
            (item.window.test_start, item.window.test_end) for item in report.windows
        ]
        assert all(run.config_version.startswith("wf-") for run in runs)
        assert session.query(BacktestBenchmark).count() == 6


def test_real_walk_forward_later_oos_failure_rolls_back_source_rows_and_default_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'walk-forward-failure.db'}"
    config_path = _write_walk_forward_config(tmp_path)
    run_alembic_upgrade(database_url, REPOSITORY_ROOT / "alembic")
    engine = create_engine(database_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _seed_walk_forward_fixture(factory)

    from vela_core.walk_forward import runner as runner_module

    original_run_backtest = runner_module.run_backtest
    oos_calls = 0

    def fail_second_oos(current_session, **kwargs):
        nonlocal oos_calls
        if kwargs["calculate_benchmarks"]:
            oos_calls += 1
            if oos_calls == 2:
                raise RuntimeError("fixed benchmark failure")
        return original_run_backtest(current_session, **kwargs)

    monkeypatch.setattr(runner_module, "run_backtest", fail_second_oos)
    default_database = REPOSITORY_ROOT / "vela.db"
    before_default = _file_identity(default_database)

    from vela_cli import main as cli

    assert (
        cli.main(
            [
                "walk-forward",
                "--config",
                str(config_path),
                "--database-url",
                database_url,
            ]
        )
        == 1
    )
    assert "fixed benchmark failure" in capsys.readouterr().err

    with factory() as session:
        assert session.query(BacktestRun).count() == 0
        assert session.query(BacktestBenchmark).count() == 0
        assert session.query(BacktestEquityCurve).count() == 0
        assert session.query(BacktestBenchmarkEquityCurve).count() == 0
        assert session.query(StrategySignal).count() == 0
        assert session.query(StrategySignalPosition).count() == 0
    assert _file_identity(default_database) == before_default


def _write_walk_forward_config(tmp_path: Path) -> Path:
    strategy_path = tmp_path / "strategy.yaml"
    strategy_path.write_text(
        """strategy_id: integration_dual_momentum
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
parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1, 2]}]
""",
        encoding="utf-8",
    )
    return config_path


def _seed_walk_forward_fixture(factory: sessionmaker) -> None:
    sessions: list[date] = []
    current = date(2017, 6, 1)
    while current <= date(2022, 1, 10):
        if current.weekday() < 5:
            sessions.append(current)
        current += timedelta(days=1)

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
            TradingCalendar(trade_date=trade_date, source="walk-forward-test")
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


def _file_identity(path: Path) -> tuple[bool, int | None]:
    return (path.exists(), path.stat().st_mtime_ns if path.exists() else None)

from __future__ import annotations

from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, TradingCalendar, WalkForwardRun, WalkForwardRunWindow
from vela_core.walk_forward.config import load_walk_forward_config
from vela_core.walk_forward.runner import WalkForwardRunner


def _config(tmp_path: Path) -> Path:
    strategy = tmp_path / "strategy.yaml"
    strategy.write_text(
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
    path = tmp_path / "walk.yaml"
    path.write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2020-01-01, end_date: 2021-12-31,
  train_years: 1, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1, 2]}]
"""
    )
    return path


def _fixed_benchmarks() -> tuple[SimpleNamespace, SimpleNamespace]:
    def benchmark(key: str) -> SimpleNamespace:
        return SimpleNamespace(
            key=key,
            name=key,
            annualized_return=SimpleNamespace(total_return=0.1, annualized_return=0.15),
            maximum_drawdown=SimpleNamespace(max_drawdown=-0.05),
            volatility=SimpleNamespace(volatility=0.12),
            sharpe_ratio=SimpleNamespace(sharpe_ratio=0.9),
            tracking_error=0.02,
            information_ratio=0.3,
            capm_alpha=0.5 if key == "csi_300_buy_hold" else None,
            capm_beta=1.1 if key == "csi_300_buy_hold" else None,
            capm_r_squared=0.8 if key == "csi_300_buy_hold" else None,
            capm_observation_count=240 if key == "csi_300_buy_hold" else None,
            up_capture_ratio=1.2,
            up_capture_observation_count=9,
            down_capture_ratio=0.7,
            down_capture_observation_count=4,
        )

    return benchmark("equal_weight_monthly"), benchmark("csi_300_buy_hold")


def _successful_backtest(config: SimpleNamespace, calculate_benchmarks: bool) -> SimpleNamespace:
    return SimpleNamespace(
        backtest_run_id=1,
        status="success",
        total_return=0.3,
        sharpe_ratio=1.0,
        annualized_return=0.2,
        max_drawdown=-0.1,
        volatility=0.22,
        benchmarks=_fixed_benchmarks() if calculate_benchmarks else (),
    )


def _seeded_session(tmp_path: Path, *, empty_calendar: bool = False) -> sessionmaker:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        if not empty_calendar:
            session.add_all(
                [
                    TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                    TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                    TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                    TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
                ]
            )
            session.commit()
    return factory


def _stub_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, int]]:
    """Record persist calls so status transitions stay on the real parent row."""
    calls: list[tuple[str, int]] = []

    def fake_persist(_session, *, run, run_id=None):
        calls.append(("persist", len(run.windows)))
        return SimpleNamespace(id=run_id)

    monkeypatch.setattr("vela_core.walk_forward.runner.persist_walk_forward_run", fake_persist)
    return calls


def test_running_row_is_committed_before_first_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = _seeded_session(tmp_path)
    config = load_walk_forward_config(_config(tmp_path))
    _stub_persistence(monkeypatch)
    windows_started: list[int] = []

    def fake_run_backtest(current_session, *, config, start_date, end_date, calculate_benchmarks):
        if not calculate_benchmarks:
            parent = current_session.scalar(
                select(WalkForwardRun).where(WalkForwardRun.status == "running")
            )
            assert parent is not None
            windows_started.append(parent.id)
        return _successful_backtest(config, calculate_benchmarks)

    monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)
    with factory() as session:
        report = WalkForwardRunner(config).run(session)

    assert len(windows_started) == 2
    assert report.walk_forward_run_id == windows_started[0]
    with factory() as session:
        parent = session.get(WalkForwardRun, report.walk_forward_run_id)
        assert parent is not None
        assert parent.status == "success"
        assert parent.finished_at is not None
        assert parent.window_count == 1
        assert parent.error_message is None


def test_success_path_passes_all_windows_to_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = _seeded_session(tmp_path)
    config = load_walk_forward_config(_config(tmp_path))
    persist_calls = _stub_persistence(monkeypatch)
    monkeypatch.setattr(
        "vela_core.walk_forward.runner.run_backtest",
        lambda current_session, *, config, start_date, end_date, calculate_benchmarks: (
            _successful_backtest(config, calculate_benchmarks)
        ),
    )
    with factory() as session:
        report = WalkForwardRunner(config).run(session)

    assert persist_calls == [("persist", 1)]
    with factory() as session:
        parent = session.get(WalkForwardRun, report.walk_forward_run_id)
        assert parent is not None
        assert parent.status == "success"
        assert parent.window_count == 1


def test_failure_path_marks_parent_failed_without_children(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = _seeded_session(tmp_path)
    config = load_walk_forward_config(_config(tmp_path))
    oos_calls = 0

    def failing_oos(current_session, *, config, start_date, end_date, calculate_benchmarks):
        nonlocal oos_calls
        if calculate_benchmarks:
            oos_calls += 1
            if oos_calls == 1:
                raise RuntimeError("fixed benchmark failure")
        return _successful_backtest(config, calculate_benchmarks)

    monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", failing_oos)
    with factory() as session:
        with pytest.raises(RuntimeError, match="fixed benchmark failure"):
            WalkForwardRunner(config).run(session)

    with factory() as session:
        parents = list(session.scalars(select(WalkForwardRun)))
        assert len(parents) == 1
        assert parents[0].status == "failed"
        assert "fixed benchmark failure" in parents[0].error_message
        assert parents[0].finished_at is not None
        assert session.scalar(select(WalkForwardRunWindow.id)) is None


def test_preflight_failure_leaves_no_parent_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = _seeded_session(tmp_path, empty_calendar=True)
    config = load_walk_forward_config(_config(tmp_path))
    monkeypatch.setattr(
        "vela_core.walk_forward.runner.run_backtest",
        lambda *args, **kwargs: _successful_backtest(
            SimpleNamespace(selection=SimpleNamespace(top_n=1)), True
        ),
    )
    with factory() as session:
        with pytest.raises(ValueError, match="calendar"):
            WalkForwardRunner(config).run(session)

    with factory() as session:
        assert session.scalar(select(WalkForwardRun.id)) is None
        assert session.scalar(select(WalkForwardRunWindow.id)) is None

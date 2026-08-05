from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from vela_core.models import Base, TradingCalendar
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


def _stub_persistence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "vela_core.walk_forward.runner.persist_walk_forward_run",
        lambda *_args, **_kwargs: SimpleNamespace(id=7),
    )


def test_runner_rejects_non_sqlite_before_search(tmp_path: Path) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    session = SimpleNamespace(
        get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    )

    with pytest.raises(ValueError, match="SQLite"):
        WalkForwardRunner(config).run(session)


def test_runner_uses_memory_snapshot_for_training_and_source_for_oos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add_all([TradingCalendar(trade_date=date(2020, 1, 2), source="test")])
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()
        calls = []

        def fake_run_backtest(
            current_session, *, config, start_date, end_date, calculate_benchmarks
        ):
            calls.append(
                (
                    current_session.bind.url.database,
                    config.version,
                    start_date,
                    end_date,
                    calculate_benchmarks,
                )
            )
            benchmarks = _fixed_benchmarks() if calculate_benchmarks else ()
            return SimpleNamespace(
                backtest_run_id=1,
                status="success",
                total_return=0.3,
                sharpe_ratio=1.0,
                annualized_return=0.2,
                max_drawdown=-0.1,
                volatility=0.22,
                benchmarks=benchmarks,
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)
        _stub_persistence(monkeypatch)
        report = WalkForwardRunner(config).run(session)

    assert len(calls) == 3
    assert calls[0][0] == ":memory:" and calls[0][4] is False
    assert calls[1][0] == ":memory:" and calls[1][4] is False
    assert calls[2][0] == str(tmp_path / "source.db") and calls[2][4] is True
    assert report.windows[0].best_combo == {"parameters.selection.top_n": 1}
    assert report.windows[0].oos_version.startswith("wf-")
    assert report.windows[0].oos_total_return == 0.3
    assert report.windows[0].oos_volatility == 0.22
    benchmark = report.windows[0].benchmarks[0]
    assert benchmark.total_return == 0.1
    assert benchmark.annualized_return == 0.15
    assert benchmark.max_drawdown == -0.05
    assert benchmark.volatility == 0.12
    assert benchmark.sharpe_ratio == 0.9
    assert benchmark.total_return_difference == pytest.approx(0.2)
    assert benchmark.annualized_return_difference == pytest.approx(0.05)


def test_runner_rejects_non_success_oos_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()

        def fake_run_backtest(
            current_session, *, config, start_date, end_date, calculate_benchmarks
        ):
            status = "success" if current_session.bind.url.database == ":memory:" else "partial"
            return SimpleNamespace(
                status=status,
                sharpe_ratio=1.0,
                annualized_return=0.2,
                max_drawdown=-0.1,
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)

        with pytest.raises(RuntimeError, match="OOS backtest returned partial"):
            WalkForwardRunner(config).run(session)


def test_failed_search_combination_rolls_back_and_later_combination_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()
        calls: list[tuple[str, int]] = []

        def fake_run_backtest(
            current_session, *, config, start_date, end_date, calculate_benchmarks
        ):
            calls.append((current_session.bind.url.database, config.selection.top_n))
            if current_session.bind.url.database == ":memory:" and config.selection.top_n == 1:
                current_session.add(TradingCalendar(trade_date=date(2020, 6, 1), source="bad"))
                raise ValueError("bad combination")
            return SimpleNamespace(
                backtest_run_id=1,
                status="success",
                sharpe_ratio=float(config.selection.top_n),
                total_return=0.3,
                annualized_return=0.2,
                max_drawdown=-0.1,
                volatility=0.22,
                benchmarks=_fixed_benchmarks() if calculate_benchmarks else (),
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)
        _stub_persistence(monkeypatch)
        report = WalkForwardRunner(config).run(session)

    assert calls == [(":memory:", 1), (":memory:", 2), (str(tmp_path / "source.db"), 2)]
    assert report.windows[0].best_combo == {"parameters.selection.top_n": 2}
    assert report.windows[0].skipped == ['{"parameters.selection.top_n":1}: bad combination']


def test_unscorable_search_combination_rolls_back_before_later_combination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()
        later_combo_saw_unscorable_write: list[bool] = []

        def fake_run_backtest(
            current_session, *, config, start_date, end_date, calculate_benchmarks
        ):
            if current_session.bind.url.database == ":memory:":
                if config.selection.top_n == 1:
                    current_session.add(
                        TradingCalendar(trade_date=date(2020, 6, 1), source="unscorable")
                    )
                    return SimpleNamespace(
                        status="partial",
                        sharpe_ratio=1.0,
                        annualized_return=0.2,
                        max_drawdown=-0.1,
                    )
                later_combo_saw_unscorable_write.append(
                    current_session.scalar(
                        select(TradingCalendar).where(TradingCalendar.source == "unscorable")
                    )
                    is not None
                )
            return SimpleNamespace(
                backtest_run_id=1,
                status="success",
                sharpe_ratio=float(config.selection.top_n),
                total_return=0.3,
                annualized_return=0.2,
                max_drawdown=-0.1,
                volatility=0.22,
                benchmarks=_fixed_benchmarks() if calculate_benchmarks else (),
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)
        _stub_persistence(monkeypatch)
        WalkForwardRunner(config).run(session)

    assert later_combo_saw_unscorable_write == [False]


def test_all_unscorable_combinations_prevent_oos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()
        calls: list[str] = []

        def fake_run_backtest(current_session, **_kwargs):
            calls.append(current_session.bind.url.database)
            return SimpleNamespace(
                status="success", sharpe_ratio=None, annualized_return=None, max_drawdown=-0.1
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)
        with pytest.raises(RuntimeError, match="no scorable"):
            WalkForwardRunner(config).run(session)

    assert calls == [":memory:", ":memory:"]


def test_runner_normalizes_selected_parameter_values_from_validated_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _config(tmp_path)
    config_path.write_text(
        config_path.read_text().replace(
            "parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1, 2]}]",
            "parameter_space: [{name: parameters.score_weights.short, type: float_range, "
            "low: 0.4, high: 0.4, step: 0.1}]",
        )
    )
    config = load_walk_forward_config(config_path)
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    with factory() as session:
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()

        def fake_run_backtest(*_args, **kwargs):
            return SimpleNamespace(
                backtest_run_id=1,
                status="success",
                total_return=0.3,
                annualized_return=0.2,
                sharpe_ratio=1.0,
                max_drawdown=-0.1,
                volatility=0.22,
                benchmarks=_fixed_benchmarks() if kwargs["calculate_benchmarks"] else (),
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)
        _stub_persistence(monkeypatch)
        report = WalkForwardRunner(config).run(session)

    assert report.windows[0].best_combo == {"parameters.score_weights.short": 0.4}
    assert type(report.windows[0].best_combo["parameters.score_weights.short"]) is float
    assert report.parameter_stability()["parameters.score_weights.short"] == {
        "value_frequencies": {"0.4": 1},
        "transition_count": 0,
        "comparison_count": 0,
        "transition_rate": None,
    }


def test_runner_rejects_successful_oos_without_persisted_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_walk_forward_config(_config(tmp_path))
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'missing-oos-id.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def benchmark(key: str) -> SimpleNamespace:
        return SimpleNamespace(
            key=key,
            name=key,
            annualized_return=SimpleNamespace(total_return=0.1, annualized_return=0.1),
            maximum_drawdown=SimpleNamespace(max_drawdown=-0.05),
            volatility=SimpleNamespace(volatility=0.1),
            sharpe_ratio=SimpleNamespace(sharpe_ratio=1.0),
            tracking_error=0.02,
            information_ratio=0.3,
        )

    with factory() as session:
        session.add_all(
            [
                TradingCalendar(trade_date=date(2020, 1, 2), source="test"),
                TradingCalendar(trade_date=date(2020, 12, 31), source="test"),
                TradingCalendar(trade_date=date(2021, 1, 4), source="test"),
                TradingCalendar(trade_date=date(2021, 12, 31), source="test"),
            ]
        )
        session.commit()

        def fake_run_backtest(current_session, **_kwargs):
            is_training = current_session.bind.url.database == ":memory:"
            return SimpleNamespace(
                status="success",
                total_return=0.1,
                annualized_return=0.1,
                sharpe_ratio=1.0,
                max_drawdown=-0.05,
                volatility=0.1,
                benchmarks=(
                    ()
                    if is_training
                    else (
                        benchmark("equal_weight_monthly"),
                        benchmark("csi_300_buy_hold"),
                    )
                ),
            )

        monkeypatch.setattr("vela_core.walk_forward.runner.run_backtest", fake_run_backtest)

        with pytest.raises(RuntimeError, match="persisted id"):
            WalkForwardRunner(config).run(session)

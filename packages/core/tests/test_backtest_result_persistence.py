from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    BacktestBenchmarkInput,
    BacktestEquityCurveInput,
    BacktestResultPersistenceResult,
    BacktestResultRunInput,
    get_backtest_result,
    persist_backtest_result,
)
from vela_core.models import (
    BacktestBenchmark,
    BacktestEquityCurve,
    BacktestRun,
    Base,
    StrategySignal,
)


def test_persist_backtest_result_writes_run_metrics_and_curve_rows() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = persist_backtest_result(
            session,
            run=_run_input(),
            equity_curve=[
                _curve_input(date(2026, 1, 2), net_value=Decimal("1.000000")),
                _curve_input(date(2026, 1, 3), net_value=Decimal("1.020000")),
            ],
        )
        session.commit()

        run = session.get(BacktestRun, result.backtest_run.id)
        curve_rows = session.query(BacktestEquityCurve).all()

    assert isinstance(result, BacktestResultPersistenceResult)
    assert run is not None
    assert run.strategy_id == "dual_momentum"
    assert run.config_version == "v1"
    assert run.start_date == date(2026, 1, 1)
    assert run.end_date == date(2026, 1, 31)
    assert run.parameters_json == '{"top_n": 2}'
    assert run.status == "success"
    assert run.total_return == Decimal("0.120000")
    assert run.annualized_return == Decimal("0.180000")
    assert run.max_drawdown == Decimal("-0.050000")
    assert run.sharpe_ratio == Decimal("1.100000")
    assert run.volatility == Decimal("0.140000")
    assert [row.backtest_run_id for row in curve_rows] == [run.id, run.id]
    assert [row.net_value for row in curve_rows] == [Decimal("1.000000"), Decimal("1.020000")]
    assert curve_rows[0].positions_json == '[{"symbol": "SPY", "weight": 1.0}]'


def test_persist_backtest_result_writes_optional_data_snapshot_without_committing() -> None:
    session_factory = _create_session_factory()
    snapshot = {
        "min_trade_date": "2026-01-01",
        "max_trade_date": "2026-01-31",
        "trading_day_count": 21,
        "active_etf_count": 2,
        "per_etf_row_counts": {"1": 21, "2": 20},
        "data_checksum": "a" * 64,
    }

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(data_snapshot_json=snapshot),
            equity_curve=[],
        )

        assert session.get(BacktestRun, persisted.backtest_run.id) is not None
        assert session.in_transaction() is True
        session.commit()
        session.expire_all()

        run = session.get(BacktestRun, persisted.backtest_run.id)

    assert run is not None
    assert run.data_snapshot_json == snapshot


def test_persist_backtest_result_preserves_rerun_history() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first = persist_backtest_result(
            session,
            run=_run_input(started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC)),
            equity_curve=[],
        )
        second = persist_backtest_result(
            session,
            run=_run_input(started_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC)),
            equity_curve=[],
        )
        session.commit()

        run_count = session.query(BacktestRun).count()

    assert first.backtest_run.id != second.backtest_run.id
    assert run_count == 2


def test_get_backtest_result_loads_run_with_ordered_equity_curve() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(),
            equity_curve=[
                _curve_input(date(2026, 1, 3), net_value=Decimal("1.020000")),
                _curve_input(date(2026, 1, 2), net_value=Decimal("1.000000")),
            ],
        )
        session.add_all(
            [
                _strategy_signal(
                    signal_date=date(2026, 1, 3),
                    backtest_run_id=persisted.backtest_run.id,
                ),
                _strategy_signal(
                    signal_date=date(2026, 1, 2),
                    backtest_run_id=persisted.backtest_run.id,
                ),
            ]
        )
        session.commit()
        session.expire_all()

        run = get_backtest_result(session, run_id=persisted.backtest_run.id)

    assert run is not None
    assert run.parameters_json == '{"top_n": 2}'
    assert [row.trade_date for row in run.equity_curve] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]
    assert [signal.signal_date for signal in run.signals] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]


def test_persist_backtest_result_loads_ordered_benchmark_curves_and_legacy_runs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        legacy = persist_backtest_result(session, run=_run_input(), equity_curve=[])
        persisted = persist_backtest_result(
            session,
            run=_run_input(started_at=datetime(2026, 2, 2, 9, 0, tzinfo=UTC)),
            equity_curve=[],
            benchmarks=[
                _benchmark(
                    "equal_weight_monthly",
                    [
                        (date(2026, 1, 3), Decimal("1.020000")),
                        (date(2026, 1, 2), Decimal("1.000000")),
                    ],
                ),
                _benchmark(
                    "csi_300_buy_hold",
                    [
                        (date(2026, 1, 3), Decimal("1.030000")),
                        (date(2026, 1, 2), Decimal("1.000000")),
                    ],
                ),
            ],
        )
        session.commit()
        session.expire_all()

        legacy_run = get_backtest_result(session, run_id=legacy.backtest_run.id)
        run = get_backtest_result(session, run_id=persisted.backtest_run.id)

    assert legacy_run is not None
    assert legacy_run.benchmarks == []
    assert run is not None
    assert [benchmark.benchmark_key for benchmark in run.benchmarks] == [
        "equal_weight_monthly",
        "csi_300_buy_hold",
    ]
    assert [point.trade_date for point in run.benchmarks[0].equity_curve] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]
    assert isinstance(run.benchmarks[0], BacktestBenchmark)


def test_persist_backtest_result_round_trips_expanded_metrics_and_isolates_reruns() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first = persist_backtest_result(
            session,
            run=_run_input(
                sortino_ratio=Decimal("2.100000"),
                calmar_ratio=Decimal("3.200000"),
                longest_drawdown_duration_sessions=4,
                longest_drawdown_peak_date=date(2026, 1, 4),
                longest_drawdown_trough_date=date(2026, 1, 6),
                longest_drawdown_recovery_date=None,
            ),
            equity_curve=[],
            benchmarks=[
                _benchmark(
                    "equal_weight_monthly",
                    [],
                    sortino_ratio=Decimal("1.100000"),
                    calmar_ratio=Decimal("1.200000"),
                    longest_drawdown_duration_sessions=2,
                    tracking_error=Decimal("0.038884"),
                    information_ratio=Decimal("12.961481"),
                ),
                _benchmark("csi_300_buy_hold", []),
            ],
        )
        second = persist_backtest_result(
            session,
            run=_run_input(
                started_at=datetime(2026, 2, 2, 9, 0, tzinfo=UTC),
                sortino_ratio=Decimal("9.900000"),
                longest_drawdown_duration_sessions=0,
            ),
            equity_curve=[],
        )
        session.commit()
        session.expire_all()

        first_run = get_backtest_result(session, run_id=first.backtest_run.id)
        second_run = get_backtest_result(session, run_id=second.backtest_run.id)

    assert first_run is not None
    assert first_run.sortino_ratio == Decimal("2.100000")
    assert first_run.calmar_ratio == Decimal("3.200000")
    assert first_run.longest_drawdown_duration_sessions == 4
    assert first_run.longest_drawdown_peak_date == date(2026, 1, 4)
    assert first_run.longest_drawdown_trough_date == date(2026, 1, 6)
    assert first_run.longest_drawdown_recovery_date is None
    assert [benchmark.benchmark_key for benchmark in first_run.benchmarks] == [
        "equal_weight_monthly",
        "csi_300_buy_hold",
    ]
    assert first_run.benchmarks[0].tracking_error == Decimal("0.038884")
    assert first_run.benchmarks[0].information_ratio == Decimal("12.961481")
    assert second_run is not None
    assert second_run.sortino_ratio == Decimal("9.900000")
    assert second_run.benchmarks == []


def test_persist_backtest_result_round_trips_benchmark_regime_metrics() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(),
            equity_curve=[],
            benchmarks=[
                _benchmark(
                    "equal_weight_monthly",
                    [],
                    up_capture_ratio=Decimal("1.995274"),
                    up_capture_observation_count=2,
                    down_capture_ratio=Decimal("0.500000"),
                    down_capture_observation_count=1,
                ),
                _benchmark(
                    "csi_300_buy_hold",
                    [],
                    capm_alpha=Decimal("11.274002"),
                    capm_beta=Decimal("2.000000"),
                    capm_r_squared=Decimal("1.000000"),
                    capm_observation_count=3,
                    up_capture_ratio=Decimal("1.995274"),
                    up_capture_observation_count=2,
                    down_capture_ratio=Decimal("0.500000"),
                    down_capture_observation_count=1,
                    tracking_error=Decimal("0.038884"),
                    information_ratio=Decimal("12.961481"),
                ),
            ],
        )
        session.commit()
        session.expire_all()

        run = get_backtest_result(session, run_id=persisted.backtest_run.id)

    assert run is not None
    equal_weight, csi_300 = run.benchmarks
    assert equal_weight.benchmark_key == "equal_weight_monthly"
    assert equal_weight.capm_alpha is None
    assert equal_weight.capm_beta is None
    assert equal_weight.capm_r_squared is None
    assert equal_weight.capm_observation_count is None
    assert equal_weight.up_capture_ratio == Decimal("1.995274")
    assert equal_weight.up_capture_observation_count == 2
    assert equal_weight.down_capture_ratio == Decimal("0.500000")
    assert equal_weight.down_capture_observation_count == 1
    assert csi_300.benchmark_key == "csi_300_buy_hold"
    assert csi_300.capm_alpha == Decimal("11.274002")
    assert csi_300.capm_beta == Decimal("2.000000")
    assert csi_300.capm_r_squared == Decimal("1.000000")
    assert csi_300.capm_observation_count == 3
    assert csi_300.up_capture_ratio == Decimal("1.995274")
    assert csi_300.up_capture_observation_count == 2
    assert csi_300.down_capture_ratio == Decimal("0.500000")
    assert csi_300.down_capture_observation_count == 1
    assert csi_300.tracking_error == Decimal("0.038884")
    assert csi_300.information_ratio == Decimal("12.961481")


def test_persist_backtest_result_rejects_duplicate_benchmark_keys_before_writing() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="keys must be unique"):
            persist_backtest_result(
                session,
                run=_run_input(),
                equity_curve=[],
                benchmarks=[
                    _benchmark("equal_weight_monthly", []),
                    _benchmark("equal_weight_monthly", []),
                ],
            )

        assert session.query(BacktestRun).count() == 0


def test_database_rejects_duplicate_benchmark_curve_dates() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(IntegrityError):
            persist_backtest_result(
                session,
                run=_run_input(),
                equity_curve=[],
                benchmarks=[
                    _benchmark(
                        "equal_weight_monthly",
                        [
                            (date(2026, 1, 2), Decimal("1.000000")),
                            (date(2026, 1, 2), Decimal("1.010000")),
                        ],
                    )
                ],
            )


def test_get_backtest_result_returns_none_for_missing_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = get_backtest_result(session, run_id=999)

    assert run is None


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _run_input(
    *,
    started_at: datetime = datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
    data_snapshot_json: dict[str, object] | None = None,
    sortino_ratio: Decimal | None = None,
    calmar_ratio: Decimal | None = None,
    longest_drawdown_duration_sessions: int | None = None,
    longest_drawdown_peak_date: date | None = None,
    longest_drawdown_trough_date: date | None = None,
    longest_drawdown_recovery_date: date | None = None,
) -> BacktestResultRunInput:
    return BacktestResultRunInput(
        strategy_id="dual_momentum",
        config_version="v1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        parameters_json='{"top_n": 2}',
        started_at=started_at,
        finished_at=datetime(2026, 2, 1, 9, 1, tzinfo=UTC),
        status="success",
        total_return=Decimal("0.120000"),
        annualized_return=Decimal("0.180000"),
        max_drawdown=Decimal("-0.050000"),
        sharpe_ratio=Decimal("1.100000"),
        volatility=Decimal("0.140000"),
        data_snapshot_json=data_snapshot_json,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        longest_drawdown_duration_sessions=longest_drawdown_duration_sessions,
        longest_drawdown_peak_date=longest_drawdown_peak_date,
        longest_drawdown_trough_date=longest_drawdown_trough_date,
        longest_drawdown_recovery_date=longest_drawdown_recovery_date,
    )


def _curve_input(
    trade_date: date,
    *,
    net_value: Decimal,
) -> BacktestEquityCurveInput:
    return BacktestEquityCurveInput(
        trade_date=trade_date,
        net_value=net_value,
        cash=Decimal("0.000000"),
        market_value=Decimal("10000.000000"),
        total_assets=Decimal("10000.000000"),
        positions_json='[{"symbol": "SPY", "weight": 1.0}]',
    )


def _benchmark(
    key: str,
    equity_curve: list[tuple[date, Decimal]],
    *,
    sortino_ratio: Decimal | None = None,
    calmar_ratio: Decimal | None = None,
    longest_drawdown_duration_sessions: int | None = None,
    tracking_error: Decimal | None = None,
    information_ratio: Decimal | None = None,
    capm_alpha: Decimal | None = None,
    capm_beta: Decimal | None = None,
    capm_r_squared: Decimal | None = None,
    capm_observation_count: int | None = None,
    up_capture_ratio: Decimal | None = None,
    up_capture_observation_count: int | None = None,
    down_capture_ratio: Decimal | None = None,
    down_capture_observation_count: int | None = None,
) -> BacktestBenchmarkInput:
    return BacktestBenchmarkInput(
        key=key,
        name=key,
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.120000"),
        max_drawdown=Decimal("-0.050000"),
        sharpe_ratio=Decimal("1.100000"),
        volatility=Decimal("0.140000"),
        equity_curve=equity_curve,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        longest_drawdown_duration_sessions=longest_drawdown_duration_sessions,
        tracking_error=tracking_error,
        information_ratio=information_ratio,
        capm_alpha=capm_alpha,
        capm_beta=capm_beta,
        capm_r_squared=capm_r_squared,
        capm_observation_count=capm_observation_count,
        up_capture_ratio=up_capture_ratio,
        up_capture_observation_count=up_capture_observation_count,
        down_capture_ratio=down_capture_ratio,
        down_capture_observation_count=down_capture_observation_count,
    )


def _strategy_signal(*, signal_date: date, backtest_run_id: int) -> StrategySignal:
    return StrategySignal(
        signal_date=signal_date,
        strategy_id="dual_momentum",
        config_version="v1",
        source="backtest",
        backtest_run_id=backtest_run_id,
        generated_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        status="success",
        result="hold",
    )

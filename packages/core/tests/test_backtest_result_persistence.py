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


def _benchmark(key: str, equity_curve: list[tuple[date, Decimal]]) -> BacktestBenchmarkInput:
    return BacktestBenchmarkInput(
        key=key,
        name=key,
        total_return=Decimal("0.100000"),
        annualized_return=Decimal("0.120000"),
        max_drawdown=Decimal("-0.050000"),
        sharpe_ratio=Decimal("1.100000"),
        volatility=Decimal("0.140000"),
        equity_curve=equity_curve,
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

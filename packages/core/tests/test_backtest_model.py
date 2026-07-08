from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy import Table, Text, UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from vela_core.models import BacktestEquityCurve, BacktestRun, Base


def test_backtest_run_table_has_required_columns() -> None:
    table = cast(Table, BacktestRun.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "strategy_id",
        "config_version",
        "start_date",
        "end_date",
        "parameters_json",
        "started_at",
        "finished_at",
        "status",
        "error_message",
        "total_return",
        "annualized_return",
        "max_drawdown",
        "sharpe_ratio",
        "volatility",
        "created_at",
        "updated_at",
    } <= columns


def test_backtest_run_optional_completion_fields_are_nullable() -> None:
    table = cast(Table, BacktestRun.__table__)

    for column_name in {
        "finished_at",
        "error_message",
        "total_return",
        "annualized_return",
        "max_drawdown",
        "sharpe_ratio",
        "volatility",
    }:
        assert table.columns[column_name].nullable is True


def test_backtest_run_uses_sqlite_compatible_text_for_parameters() -> None:
    table = cast(Table, BacktestRun.__table__)

    assert isinstance(table.columns["parameters_json"].type, Text)


def test_backtest_run_supports_expected_status_values() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _backtest_run(status=status, config_version=f"v1-{status}")
                for status in BacktestRun.STATUSES
            ]
        )
        session.commit()

        statuses = {run.status for run in session.query(BacktestRun).all()}

    assert statuses == {"running", "success", "failed", "partial"}


def test_backtest_run_stores_serialized_parameters() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(_backtest_run(parameters_json='{"rebalance": "monthly"}'))
        session.commit()

        run = session.query(BacktestRun).one()

    assert run.parameters_json == '{"rebalance": "monthly"}'


def test_backtest_run_allows_same_strategy_config_and_date_range_rerun() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _backtest_run(started_at=datetime(2026, 6, 18, 9, 30, tzinfo=UTC)),
                _backtest_run(started_at=datetime(2026, 6, 18, 9, 35, tzinfo=UTC)),
            ]
        )
        session.commit()

        assert session.query(BacktestRun).count() == 2


def test_backtest_run_has_lookup_indexes() -> None:
    table = cast(Table, BacktestRun.__table__)
    indexed_columns = {tuple(column.name for column in index.columns) for index in table.indexes}

    assert ("strategy_id", "config_version") in indexed_columns
    assert ("status", "started_at") in indexed_columns
    assert ("start_date", "end_date") in indexed_columns


def test_backtest_equity_curve_table_has_required_columns() -> None:
    table = cast(Table, BacktestEquityCurve.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "backtest_run_id",
        "trade_date",
        "net_value",
        "cash",
        "market_value",
        "total_assets",
        "positions_json",
        "created_at",
    } <= columns


def test_backtest_equity_curve_uses_sqlite_compatible_text_for_positions() -> None:
    table = cast(Table, BacktestEquityCurve.__table__)

    assert isinstance(table.columns["positions_json"].type, Text)


def test_backtest_equity_curve_references_backtest_run() -> None:
    table = cast(Table, BacktestEquityCurve.__table__)
    foreign_keys = table.columns["backtest_run_id"].foreign_keys

    assert any(foreign_key.column.table.name == "backtest_run" for foreign_key in foreign_keys)


def test_backtest_equity_curve_has_run_trade_date_unique_constraint() -> None:
    table = cast(Table, BacktestEquityCurve.__table__)
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        {column.name for column in constraint.columns} == {"backtest_run_id", "trade_date"}
        for constraint in unique_constraints
    )


def test_backtest_equity_curve_rejects_duplicate_run_trade_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        session.add(_backtest_equity_curve(backtest_run_id=run.id, net_value=Decimal("1.000000")))
        session.commit()

        session.add(_backtest_equity_curve(backtest_run_id=run.id, net_value=Decimal("1.010000")))
        with pytest.raises(IntegrityError):
            session.commit()


def test_backtest_equity_curve_allows_same_trade_date_for_different_runs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first_run = _add_backtest_run(session, config_version="v1")
        second_run = _add_backtest_run(session, config_version="v2")
        session.add_all(
            [
                _backtest_equity_curve(backtest_run_id=first_run.id),
                _backtest_equity_curve(backtest_run_id=second_run.id),
            ]
        )
        session.commit()

        assert session.query(BacktestEquityCurve).count() == 2


def test_backtest_equity_curve_has_lookup_indexes() -> None:
    table = cast(Table, BacktestEquityCurve.__table__)
    indexed_columns = {tuple(column.name for column in index.columns) for index in table.indexes}

    assert ("backtest_run_id", "trade_date") in indexed_columns


def test_backtest_run_equity_curve_returns_related_curve_rows() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        expected_dates = {date(2026, 1, 2), date(2026, 1, 3)}
        session.add_all(
            [
                _backtest_equity_curve(
                    backtest_run_id=run.id,
                    trade_date=date(2026, 1, 2),
                ),
                _backtest_equity_curve(
                    backtest_run_id=run.id,
                    trade_date=date(2026, 1, 3),
                ),
            ]
        )
        session.commit()

        curve_dates = {point.trade_date for point in run.equity_curve}

    assert curve_dates == expected_dates


def test_backtest_equity_curve_backtest_run_returns_parent_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        expected_run_id = run.id
        curve = _backtest_equity_curve(backtest_run_id=run.id)
        session.add(curve)
        session.commit()

        parent_run_id = curve.backtest_run.id

    assert parent_run_id == expected_run_id


def test_alembic_target_metadata_includes_backtest_tables() -> None:
    import importlib.util
    from pathlib import Path

    env_path = Path(__file__).parents[3] / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)

    assert spec is not None
    assert spec.loader is not None

    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)

    assert "backtest_run" in alembic_env.target_metadata.tables
    assert "backtest_equity_curve" in alembic_env.target_metadata.tables
    assert "backtest_equity_point" not in alembic_env.target_metadata.tables


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _add_backtest_run(session: Session, config_version: str = "v1") -> BacktestRun:
    run = _backtest_run(config_version=config_version)
    session.add(run)
    session.flush()
    return run


def _backtest_run(
    *,
    strategy_id: str = "dual_momentum",
    config_version: str = "v1",
    start_date: date = date(2020, 1, 1),
    end_date: date = date(2026, 6, 18),
    parameters_json: str = '{"rebalance": "monthly", "top_n": 2}',
    started_at: datetime = datetime(2026, 6, 18, 9, 30, tzinfo=UTC),
    finished_at: datetime | None = datetime(2026, 6, 18, 9, 31, tzinfo=UTC),
    status: str = "success",
    error_message: str | None = None,
    total_return: Decimal | None = Decimal("0.250000"),
    annualized_return: Decimal | None = Decimal("0.080000"),
    max_drawdown: Decimal | None = Decimal("-0.120000"),
    sharpe_ratio: Decimal | None = Decimal("1.100000"),
    volatility: Decimal | None = Decimal("0.150000"),
) -> BacktestRun:
    return BacktestRun(
        strategy_id=strategy_id,
        config_version=config_version,
        start_date=start_date,
        end_date=end_date,
        parameters_json=parameters_json,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        error_message=error_message,
        total_return=total_return,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        volatility=volatility,
    )


def _backtest_equity_curve(
    *,
    backtest_run_id: int,
    trade_date: date = date(2026, 1, 2),
    net_value: Decimal = Decimal("1.000000"),
    cash: Decimal = Decimal("1000.000000"),
    market_value: Decimal = Decimal("9000.000000"),
    total_assets: Decimal = Decimal("10000.000000"),
    positions_json: str = '[{"symbol": "SPY", "weight": 0.9}]',
) -> BacktestEquityCurve:
    return BacktestEquityCurve(
        backtest_run_id=backtest_run_id,
        trade_date=trade_date,
        net_value=net_value,
        cash=cash,
        market_value=market_value,
        total_assets=total_assets,
        positions_json=positions_json,
    )

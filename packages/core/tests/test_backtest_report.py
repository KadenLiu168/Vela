from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    BacktestEquityCurveInput,
    BacktestReportNotFoundError,
    BacktestResultRunInput,
    export_backtest_report,
    persist_backtest_result,
)
from vela_core.models import Base


def test_export_backtest_report_formats_metrics_and_curve_summary() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(),
            equity_curve=[
                _curve_input(date(2026, 1, 1), net_value=Decimal("1.000000")),
                _curve_input(date(2026, 1, 2), net_value=Decimal("0.950000")),
                _curve_input(date(2026, 1, 3), net_value=Decimal("1.120000")),
            ],
        )
        session.commit()

        report = export_backtest_report(session, run_id=persisted.backtest_run.id)

    assert "Backtest Report" in report
    assert f"Run id: {persisted.backtest_run.id}" in report
    assert "Strategy: dual_momentum" in report
    assert "Config version: v1" in report
    assert "Date range: 2026-01-01 to 2026-01-31" in report
    assert "Status: success" in report
    assert 'Parameters: {"top_n": 2}' in report
    assert "- Total return: 0.120000" in report
    assert "- Annualized return: 0.180000" in report
    assert "- Max drawdown: -0.050000" in report
    assert "- Volatility: 0.140000" in report
    assert "- Sharpe ratio: 1.100000" in report
    assert "- Points: 3" in report
    assert "- First: 2026-01-01 net_value=1.000000" in report
    assert "- Last: 2026-01-03 net_value=1.120000" in report
    assert "- Min net value: 2026-01-02 net_value=0.950000" in report
    assert "- Max net value: 2026-01-03 net_value=1.120000" in report


def test_export_backtest_report_formats_empty_equity_curve() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(status="failed", error_message="No local market prices"),
            equity_curve=[],
        )
        session.commit()

        report = export_backtest_report(session, run_id=persisted.backtest_run.id)

    assert "Status: failed" in report
    assert "Error: No local market prices" in report
    assert "- Points: 0" in report
    assert "- Rows: none" in report


def test_export_backtest_report_raises_for_missing_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(BacktestReportNotFoundError, match="Backtest run not found: 999"):
            export_backtest_report(session, run_id=999)


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _run_input(
    *,
    status: str = "success",
    error_message: str | None = None,
) -> BacktestResultRunInput:
    return BacktestResultRunInput(
        strategy_name="dual_momentum",
        config_version="v1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        parameters_json='{"top_n": 2}',
        started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 2, 1, 9, 1, tzinfo=UTC),
        status=status,
        error_message=error_message,
        total_return=Decimal("0.120000"),
        annualized_return=Decimal("0.180000"),
        max_drawdown=Decimal("-0.050000"),
        sharpe_ratio=Decimal("1.100000"),
        volatility=Decimal("0.140000"),
    )


def _curve_input(trade_date: date, *, net_value: Decimal) -> BacktestEquityCurveInput:
    return BacktestEquityCurveInput(
        trade_date=trade_date,
        net_value=net_value,
        cash=Decimal("0.000000"),
        market_value=net_value,
        total_assets=net_value,
        positions_json='[{"etf_id": 1, "target_weight": "1.000000"}]',
    )

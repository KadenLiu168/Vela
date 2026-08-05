from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    BacktestBenchmarkInput,
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
            benchmarks=[
                BacktestBenchmarkInput(
                    key="equal_weight_monthly",
                    name="Equal-weight monthly rebalanced portfolio",
                    total_return=Decimal("0.100000"),
                    annualized_return=Decimal("0.150000"),
                    max_drawdown=Decimal("-0.040000"),
                    sharpe_ratio=Decimal("0.900000"),
                    volatility=Decimal("0.120000"),
                    equity_curve=[],
                    sortino_ratio=Decimal("0.700000"),
                    calmar_ratio=Decimal("1.300000"),
                    longest_drawdown_duration_sessions=2,
                    longest_drawdown_peak_date=date(2026, 1, 12),
                    longest_drawdown_trough_date=date(2026, 1, 18),
                    longest_drawdown_recovery_date=None,
                    tracking_error=Decimal("0.038884"),
                    information_ratio=Decimal("12.961481"),
                )
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
    assert "- Sortino (rf MAR, 252D): 1.200000" in report
    assert "- Calmar (calendar CAGR / |MaxDD|): 2.400000" in report
    assert "- Longest drawdown duration (official sessions): 3" in report
    assert "- Longest drawdown peak: 2026-01-10" in report
    assert "- Longest drawdown trough: 2026-01-20" in report
    assert "- Longest drawdown recovery: ongoing" in report
    assert "- Points: 3" in report
    assert "- First: 2026-01-01 net_value=1.000000" in report
    assert "- Last: 2026-01-03 net_value=1.120000" in report
    assert "- Min net value: 2026-01-02 net_value=0.950000" in report
    assert "- Max net value: 2026-01-03 net_value=1.120000" in report
    assert "Benchmark: Equal-weight monthly rebalanced portfolio" in report
    assert "- Total return: 0.100000" in report
    assert "- Annualized return: 0.150000" in report
    assert "- Max drawdown: -0.040000" in report
    assert "- Volatility: 0.120000" in report
    assert "- Sharpe ratio: 0.900000" in report
    assert "- Sortino (rf MAR, 252D): 0.700000" in report
    assert "- Calmar (calendar CAGR / |MaxDD|): 1.300000" in report
    assert "- Longest drawdown duration (official sessions): 2" in report
    assert "- Longest drawdown peak: 2026-01-12" in report
    assert "- Longest drawdown trough: 2026-01-18" in report
    assert "- Longest drawdown recovery: ongoing" in report
    assert "- Tracking error (252D): 0.038884" in report
    assert "- Information ratio (252D): 12.961481" in report
    assert "- Strategy total return difference: 0.020000" in report
    assert "- Strategy annualized return difference: 0.030000" in report


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


def test_export_backtest_report_keeps_legacy_expanded_metrics_unavailable() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(expanded_metrics=False),
            equity_curve=[],
            benchmarks=[
                BacktestBenchmarkInput(
                    key="equal_weight_monthly",
                    name="Equal-weight monthly rebalanced portfolio",
                    total_return=Decimal("0.100000"),
                    annualized_return=Decimal("0.150000"),
                    max_drawdown=Decimal("-0.040000"),
                    sharpe_ratio=Decimal("0.900000"),
                    volatility=Decimal("0.120000"),
                    equity_curve=[],
                )
            ],
        )
        session.commit()

        report = export_backtest_report(session, run_id=persisted.backtest_run.id)

    assert "- Sortino (rf MAR, 252D): n/a" in report
    assert "- Calmar (calendar CAGR / |MaxDD|): n/a" in report
    assert "- Longest drawdown duration (official sessions): n/a" in report
    assert "- Longest drawdown recovery: n/a" in report
    assert "- Tracking error (252D): n/a" in report
    assert "- Information ratio (252D): n/a" in report


def test_export_backtest_report_raises_for_missing_run() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(BacktestReportNotFoundError, match="Backtest run not found: 999"):
            export_backtest_report(session, run_id=999)


def test_export_backtest_report_formats_benchmark_regime_metrics() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(),
            equity_curve=[],
            benchmarks=[
                BacktestBenchmarkInput(
                    key="equal_weight_monthly",
                    name="Equal-weight monthly rebalanced portfolio",
                    total_return=Decimal("0.100000"),
                    annualized_return=Decimal("0.150000"),
                    max_drawdown=Decimal("-0.040000"),
                    sharpe_ratio=Decimal("0.900000"),
                    volatility=Decimal("0.120000"),
                    equity_curve=[],
                    up_capture_ratio=Decimal("1.995274"),
                    up_capture_observation_count=2,
                    down_capture_ratio=Decimal("0.500000"),
                    down_capture_observation_count=1,
                ),
                BacktestBenchmarkInput(
                    key="csi_300_buy_hold",
                    name="CSI 300 buy-and-hold",
                    total_return=Decimal("0.100000"),
                    annualized_return=Decimal("0.150000"),
                    max_drawdown=Decimal("-0.040000"),
                    sharpe_ratio=Decimal("0.900000"),
                    volatility=Decimal("0.120000"),
                    equity_curve=[],
                    capm_alpha=Decimal("11.274002"),
                    capm_beta=Decimal("2.000000"),
                    capm_r_squared=Decimal("0.958580"),
                    capm_observation_count=4,
                    up_capture_ratio=Decimal("1.995274"),
                    up_capture_observation_count=2,
                    down_capture_ratio=Decimal("0.500000"),
                    down_capture_observation_count=1,
                ),
            ],
        )
        session.commit()

        report = export_backtest_report(session, run_id=persisted.backtest_run.id)

    assert "- CSI 300 ETF proxy Alpha (252D compounded): 11.274002" in report
    assert "- CSI 300 ETF proxy Beta: 2.000000" in report
    assert "- CSI 300 ETF proxy R-squared: 0.958580" in report
    assert "- CAPM observation count (daily sessions): 4" in report
    assert report.count("- Monthly Up Capture ratio (benchmark up months): 1.995274") == 2
    assert report.count("- Up capture selected months: 2") == 2
    assert report.count("- Monthly Down Capture ratio (benchmark down months): 0.500000") == 2
    assert report.count("- Down capture selected months: 1") == 2
    assert "- CSI 300 ETF proxy Alpha (252D compounded):" in report


def test_export_backtest_report_keeps_legacy_regime_metrics_null() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persisted = persist_backtest_result(
            session,
            run=_run_input(expanded_metrics=False),
            equity_curve=[],
            benchmarks=[
                BacktestBenchmarkInput(
                    key="csi_300_buy_hold",
                    name="CSI 300 buy-and-hold",
                    total_return=Decimal("0.100000"),
                    annualized_return=Decimal("0.150000"),
                    max_drawdown=Decimal("-0.040000"),
                    sharpe_ratio=Decimal("0.900000"),
                    volatility=Decimal("0.120000"),
                    equity_curve=[],
                )
            ],
        )
        session.commit()

        report = export_backtest_report(session, run_id=persisted.backtest_run.id)

    assert "- CSI 300 ETF proxy Alpha (252D compounded): n/a" in report
    assert "- CSI 300 ETF proxy Beta: n/a" in report
    assert "- CSI 300 ETF proxy R-squared: n/a" in report
    assert "- CAPM observation count (daily sessions): n/a" in report
    assert "- Monthly Up Capture ratio (benchmark up months): n/a" in report
    assert "- Up capture selected months: n/a" in report
    assert "- Monthly Down Capture ratio (benchmark down months): n/a" in report
    assert "- Down capture selected months: n/a" in report


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _run_input(
    *,
    status: str = "success",
    error_message: str | None = None,
    expanded_metrics: bool = True,
) -> BacktestResultRunInput:
    return BacktestResultRunInput(
        strategy_id="dual_momentum",
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
        sortino_ratio=Decimal("1.200000") if expanded_metrics else None,
        calmar_ratio=Decimal("2.400000") if expanded_metrics else None,
        longest_drawdown_duration_sessions=3 if expanded_metrics else None,
        longest_drawdown_peak_date=date(2026, 1, 10) if expanded_metrics else None,
        longest_drawdown_trough_date=date(2026, 1, 20) if expanded_metrics else None,
        longest_drawdown_recovery_date=None,
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

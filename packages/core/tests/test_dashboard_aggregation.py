from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import get_dashboard_summary
from vela_core.models import (
    BacktestBenchmark,
    BacktestRun,
    Base,
    DataFetchLog,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    StrategySignalPosition,
    WalkForwardRun,
)


def test_dashboard_summary_reports_empty_persisted_workflow_data() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    assert summary == {
        "strategy": {"strategy_id": "Dual_momentum", "version": "v1"},
        "market_data": {
            "price_rows": 0,
            "covered_etfs": 0,
            "earliest_trade_date": None,
            "latest_trade_date": None,
            "etf_list": [],
        },
        "latest_signal": None,
        "recent_backtest": None,
        "latest_walk_forward": None,
        "recent_fetch_logs": [],
    }


def test_dashboard_summary_aggregates_persisted_sqlite_rows() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        session.add_all(
            [
                _market_price(spy.id, trade_date=date(2026, 6, 22)),
                _market_price(spy.id, trade_date=date(2026, 6, 23)),
                _market_price(qqq.id, trade_date=date(2026, 6, 23)),
                StrategySignal(
                    signal_date=date(2026, 6, 22),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                    status="success",
                    result="hold",
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[
                        StrategySignalPosition(
                            etf_id=spy.id,
                            rank=1,
                            score=Decimal("0.800000"),
                            target_weight=Decimal("0.500000"),
                        ),
                        StrategySignalPosition(
                            etf_id=qqq.id,
                            rank=2,
                            score=Decimal("0.700000"),
                            target_weight=Decimal("0.500000"),
                        ),
                    ],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 24),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
                    status="failed",
                    result=None,
                    error_message="No active ETFs found",
                ),
                BacktestRun(
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31),
                    parameters_json='{"top_n": 2}',
                    started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 2, 1, 9, 1, tzinfo=UTC),
                    status="success",
                    total_return=Decimal("0.120000"),
                    max_drawdown=Decimal("-0.050000"),
                    sharpe_ratio=Decimal("1.100000"),
                ),
                _data_fetch_log(
                    fetch_mode="incremental",
                    status="partial",
                    started_at=datetime(2026, 6, 24, 8, 59, tzinfo=UTC),
                    finished_at=datetime(2026, 6, 24, 9, 0, tzinfo=UTC),
                    rows_fetched=25,
                    rows_inserted=20,
                    rows_updated=5,
                    error_message="QQQ: provider timeout",
                ),
                _data_fetch_log(
                    fetch_mode="full",
                    status="success",
                    started_at=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 6, 23, 8, 5, tzinfo=UTC),
                    rows_fetched=100,
                    rows_inserted=90,
                    rows_updated=10,
                    error_message=None,
                ),
                _data_fetch_log(
                    target_type="etf_info",
                    fetch_mode="incremental",
                    status="success",
                    started_at=datetime(2026, 6, 25, 8, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 6, 25, 8, 1, tzinfo=UTC),
                    rows_fetched=1,
                    rows_inserted=1,
                    rows_updated=0,
                    error_message=None,
                ),
            ]
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    assert summary == {
        "strategy": {"strategy_id": "Dual_momentum", "version": "v1"},
        "market_data": {
            "price_rows": 3,
            "covered_etfs": 2,
            "earliest_trade_date": "2026-06-22",
            "latest_trade_date": "2026-06-23",
            "etf_list": [
                {
                    "etf_id": qqq.id,
                    "exchange": "NYSEARCA",
                    "symbol": "QQQ",
                    "name": "QQQ ETF",
                    "category": None,
                    "earliest_trade_date": "2026-06-23",
                },
                {
                    "etf_id": spy.id,
                    "exchange": "NYSEARCA",
                    "symbol": "SPY",
                    "name": "SPY ETF",
                    "category": None,
                    "earliest_trade_date": "2026-06-22",
                },
            ],
        },
        "latest_signal": {
            "signal_id": 2,
            "signal_date": "2026-06-23",
            "config_version": "v1",
            "status": "success",
            "result": "rebalance",
            "generated_at": "2026-06-23T09:30:00",
            "is_fallback": False,
            "position_count": 2,
            "source": "manual",
            "backtest_run_id": None,
            "positions": [
                {
                    "exchange": "NYSEARCA",
                    "symbol": "SPY",
                    "name": "SPY ETF",
                    "target_weight": "0.500000",
                    "rank": 1,
                    "score": "0.800000",
                    "is_fallback": False,
                },
                {
                    "exchange": "NYSEARCA",
                    "symbol": "QQQ",
                    "name": "QQQ ETF",
                    "target_weight": "0.500000",
                    "rank": 2,
                    "score": "0.700000",
                    "is_fallback": False,
                },
            ],
        },
        "recent_backtest": {
            "run_id": 1,
            "strategy_id": "Dual_momentum",
            "config_version": "v1",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "status": "success",
            "total_return": "0.120000",
            "annualized_return": None,
            "max_drawdown": "-0.050000",
            "sharpe_ratio": "1.100000",
            "started_at": "2026-02-01T09:00:00",
            "benchmarks": [],
        },
        "latest_walk_forward": None,
        "recent_fetch_logs": [
            {
                "fetch_log_id": 1,
                "fetch_time": "2026-06-24T09:00:00",
                "mode": "incremental",
                "status": "partial",
                "rows_fetched": 25,
                "rows_inserted": 20,
                "rows_updated": 5,
                "error_summary": "QQQ: provider timeout",
            },
            {
                "fetch_log_id": 2,
                "fetch_time": "2026-06-23T08:05:00",
                "mode": "full",
                "status": "success",
                "rows_fetched": 100,
                "rows_inserted": 90,
                "rows_updated": 10,
                "error_summary": None,
            },
        ],
    }


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _strategy_summary() -> dict[str, str]:
    return {"strategy_id": "Dual_momentum", "version": "v1"}


def test_dashboard_summary_ignores_newer_foreign_strategy_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        matching = StrategySignal(
            signal_date=date(2026, 6, 23),
            strategy_id="Dual_momentum",
            config_version="v1",
            source="manual",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
        )
        session.add_all(
            [
                matching,
                StrategySignal(
                    signal_date=date(2026, 6, 24),
                    strategy_id="Other_strategy",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
                    status="success",
                    result="hold",
                ),
            ]
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_signal = summary["latest_signal"]
    assert isinstance(latest_signal, dict)
    assert latest_signal["signal_id"] == matching.id


def test_dashboard_summary_reports_empty_latest_signal_without_successful_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 23),
                strategy_id="Dual_momentum",
                config_version="v1",
                source="manual",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="failed",
                result=None,
                error_message="No active ETFs found",
            )
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    assert summary["latest_signal"] is None


def test_dashboard_summary_marks_latest_signal_fallback() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        defensive = _add_etf(session, symbol="SHY")
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 23),
                strategy_id="Dual_momentum",
                config_version="v1",
                source="manual",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="success",
                result="rebalance",
                positions=[
                    StrategySignalPosition(
                        etf_id=defensive.id,
                        rank=None,
                        score=None,
                        target_weight=Decimal("1.000000"),
                    )
                ],
            )
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_signal = summary["latest_signal"]
    assert isinstance(latest_signal, dict)
    assert latest_signal["is_fallback"] is True


def test_dashboard_summary_orders_unranked_signal_positions_last() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        ranked = _add_etf(session, symbol="SPY")
        unranked = _add_etf(session, symbol="SHY")
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 23),
                strategy_id="Dual_momentum",
                config_version="v1",
                source="manual",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="success",
                result="rebalance",
                positions=[
                    StrategySignalPosition(
                        etf_id=unranked.id,
                        rank=None,
                        score=None,
                        target_weight=Decimal("0.400000"),
                    ),
                    StrategySignalPosition(
                        etf_id=ranked.id,
                        rank=1,
                        score=Decimal("0.800000"),
                        target_weight=Decimal("0.600000"),
                    ),
                ],
            )
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_signal = summary["latest_signal"]
    assert isinstance(latest_signal, dict)
    assert latest_signal["positions"] == [
        {
            "exchange": "NYSEARCA",
            "symbol": "SPY",
            "name": "SPY ETF",
            "target_weight": "0.600000",
            "rank": 1,
            "score": "0.800000",
            "is_fallback": False,
        },
        {
            "exchange": "NYSEARCA",
            "symbol": "SHY",
            "name": "SHY ETF",
            "target_weight": "0.400000",
            "rank": None,
            "score": None,
            "is_fallback": True,
        },
    ]


def test_dashboard_summary_reports_successful_signal_without_positions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 23),
                strategy_id="Dual_momentum",
                config_version="v1",
                source="manual",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="success",
                result="empty",
            )
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_signal = summary["latest_signal"]
    assert isinstance(latest_signal, dict)
    assert latest_signal["position_count"] == 0
    assert latest_signal["positions"] == []


def test_dashboard_summary_ignores_foreign_strategy_backtest_runs() -> None:
    """The decision surface pairs the recent backtest with the current
    strategy's signal, so another strategy's run must never be reported as this
    strategy's most recent performance."""
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            BacktestRun(
                strategy_id="Other_strategy",
                config_version="v1",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                parameters_json='{"top_n": 2}',
                started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                finished_at=datetime(2026, 2, 1, 9, 1, tzinfo=UTC),
                status="success",
                total_return=Decimal("0.120000"),
            )
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    assert summary["recent_backtest"] is None


def test_dashboard_summary_projects_recent_backtest_benchmarks() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = BacktestRun(
            strategy_id="Dual_momentum",
            config_version="v1",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            parameters_json='{"top_n": 2}',
            started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 1, 9, 1, tzinfo=UTC),
            status="success",
            total_return=Decimal("0.120000"),
            annualized_return=Decimal("0.100000"),
        )
        session.add(run)
        session.flush()
        session.add(
            BacktestBenchmark(
                backtest_run_id=run.id,
                benchmark_key="csi_300_buy_hold",
                display_name="CSI 300 buy-and-hold",
                total_return=Decimal("0.050000"),
                annualized_return=Decimal("0.040000"),
                max_drawdown=Decimal("-0.200000"),
                sharpe_ratio=Decimal("0.300000"),
            )
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    recent_backtest = summary["recent_backtest"]
    assert isinstance(recent_backtest, dict)
    assert recent_backtest["benchmarks"] == [
        {
            "key": "csi_300_buy_hold",
            "name": "CSI 300 buy-and-hold",
            "total_return": "0.050000",
            "total_return_difference": "0.070000",
            "annualized_return_difference": "0.060000",
            "sharpe_ratio": "0.300000",
            "max_drawdown": "-0.200000",
        }
    ]


def test_dashboard_summary_projects_successful_walk_forward_evidence() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        _add_walk_forward_run(session, strategy_id="Dual_momentum", status="success")
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_walk_forward = summary["latest_walk_forward"]
    assert isinstance(latest_walk_forward, dict)
    assert latest_walk_forward["status"] == "success"
    assert latest_walk_forward["window_count"] == 3
    assert latest_walk_forward["finished_at"] == "2026-02-01T09:00:00"
    assert latest_walk_forward["oos"] == {
        "metrics": {
            "total_return": _evidence_summary(),
            "sharpe_ratio": _evidence_summary(),
            "max_drawdown": _evidence_summary(),
        },
        "positive_window_rate": _evidence_rate(),
        "generalization_gap": _evidence_summary(),
        "benchmarks": {
            "equal_weight_monthly": {"outperformance_rate": _evidence_rate()},
            "csi_300_buy_hold": {"outperformance_rate": _evidence_rate()},
        },
    }


def test_dashboard_summary_withholds_walk_forward_evidence_for_non_success_runs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        _add_walk_forward_run(
            session,
            strategy_id="Dual_momentum",
            status="failed",
            error_message="provider unavailable",
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_walk_forward = summary["latest_walk_forward"]
    assert isinstance(latest_walk_forward, dict)
    assert latest_walk_forward["status"] == "failed"
    assert latest_walk_forward["error_message"] == "provider unavailable"
    assert latest_walk_forward["oos"] is None


def test_dashboard_summary_prefers_active_walk_forward_run_over_finished_one() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        _add_walk_forward_run(
            session,
            strategy_id="Dual_momentum",
            status="success",
            finished_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        )
        _add_walk_forward_run(
            session,
            strategy_id="Dual_momentum",
            status="queued",
            finished_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
        )
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    latest_walk_forward = summary["latest_walk_forward"]
    assert isinstance(latest_walk_forward, dict)
    assert latest_walk_forward["status"] == "queued"
    assert latest_walk_forward["oos"] is None


def test_dashboard_summary_ignores_foreign_strategy_walk_forward_runs() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        _add_walk_forward_run(session, strategy_id="Other_strategy", status="success")
        session.commit()

        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    assert summary["latest_walk_forward"] is None


def _evidence_summary(
    *, median: float = 0.1, window_count: int = 3, valid_count: int = 3
) -> dict[str, object]:
    return {
        "median": median,
        "mean": 0.1,
        "window_count": window_count,
        "valid_count": valid_count,
        "evidence_status": "sufficient",
    }


def _evidence_rate() -> dict[str, object]:
    return {
        "value": 1.0,
        "numerator": 3,
        "denominator": 3,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }


def _walk_forward_evidence() -> dict[str, object]:
    summary = _evidence_summary()
    summary_extended = {**summary, "min": 0.1, "max": 0.1, "std": 0.0}
    rate = _evidence_rate()
    benchmark = {
        "total_return_difference": summary_extended,
        "annualized_return_difference": summary_extended,
        "tracking_error": summary_extended,
        "information_ratio": summary_extended,
        "outperformance_rate": rate,
    }
    return {
        "metrics": {
            name: summary_extended
            for name in (
                "total_return",
                "annualized_return",
                "sharpe_ratio",
                "max_drawdown",
                "volatility",
                "sortino_ratio",
                "calmar_ratio",
                "longest_drawdown_duration_sessions",
            )
        },
        "positive_window_rate": rate,
        "generalization_gap": summary_extended,
        "benchmarks": {"equal_weight_monthly": benchmark, "csi_300_buy_hold": benchmark},
        "parameter_stability": {},
    }


def _add_walk_forward_run(
    session: Session,
    *,
    strategy_id: str,
    status: str,
    finished_at: datetime | None = None,
    error_message: str | None = None,
) -> WalkForwardRun:
    row = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=3,
        walk_forward_config_json={"window": {}},
        base_strategy_config_json={"strategy_id": strategy_id},
        provenance_version="wf_provenance_v1",
        config_checksum="a" * 64,
        input_data_snapshot_json={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2026-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2026-01-01"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence_version="wf_evidence_v1",
        evidence_json=_walk_forward_evidence(),
        status=status,
        error_message=error_message,
        started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        finished_at=finished_at or datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
    )
    session.add(row)
    session.flush()
    return row


def _add_etf(session: Session, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf


def _market_price(etf_id: int, *, trade_date: date) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=Decimal("100.000000"),
        high_price=Decimal("101.000000"),
        low_price=Decimal("99.000000"),
        close_price=Decimal("100.000000"),
        factor_hfq=Decimal("1"),
        volume=1000,
    )


def _data_fetch_log(
    *,
    target_type: str = "market_price",
    fetch_mode: str,
    status: str,
    started_at: datetime,
    finished_at: datetime | None,
    rows_fetched: int | None,
    rows_inserted: int | None,
    rows_updated: int | None,
    error_message: str | None,
) -> DataFetchLog:
    return DataFetchLog(
        source="tencent",
        target_type=target_type,
        fetch_mode=fetch_mode,
        range_start=None,
        range_end=None,
        requested_symbols=None,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        rows_fetched=rows_fetched,
        rows_inserted=rows_inserted,
        rows_updated=rows_updated,
        error_message=error_message,
    )

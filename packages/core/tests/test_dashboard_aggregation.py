from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import get_dashboard_summary
from vela_core.models import (
    BacktestRun,
    Base,
    DataFetchLog,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    StrategySignalPosition,
)


def test_dashboard_summary_reports_empty_persisted_workflow_data() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        summary = get_dashboard_summary(session, strategy_summary=_strategy_summary())

    assert summary == {
        "strategy": {"strategy_id": "dual_momentum", "version": "v1"},
        "market_data": {
            "price_rows": 0,
            "covered_etfs": 0,
            "earliest_trade_date": None,
            "latest_trade_date": None,
            "etf_list": [],
        },
        "latest_signal": None,
        "recent_backtest": None,
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
                    generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                    status="success",
                    result="hold",
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                    config_version="v1",
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
                    generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
                    status="failed",
                    result=None,
                    error_message="No active ETFs found",
                ),
                BacktestRun(
                    strategy_id="dual_momentum",
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
        "strategy": {"strategy_id": "dual_momentum", "version": "v1"},
        "market_data": {
            "price_rows": 3,
            "covered_etfs": 2,
            "earliest_trade_date": "2026-06-22",
            "latest_trade_date": "2026-06-23",
            "etf_list": [
                {
                    "exchange": "NYSEARCA",
                    "symbol": "QQQ",
                    "name": "QQQ ETF",
                    "category": None,
                    "earliest_trade_date": "2026-06-23",
                },
                {
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
        },
        "recent_backtest": {
            "run_id": 1,
            "strategy_id": "dual_momentum",
            "config_version": "v1",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "status": "success",
            "total_return": "0.120000",
            "max_drawdown": "-0.050000",
            "sharpe_ratio": "1.100000",
            "started_at": "2026-02-01T09:00:00",
        },
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
    return {"strategy_id": "dual_momentum", "version": "v1"}


def test_dashboard_summary_reports_empty_latest_signal_without_successful_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                config_version="v1",
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
        source="akshare",
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

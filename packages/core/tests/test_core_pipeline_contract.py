import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pandas as pd
from sqlalchemy import select
from vela_core import (
    fetch_full_market_prices,
    generate_and_persist_strategy_signal,
    get_backtest_result,
    get_dashboard_summary,
    run_alembic_upgrade,
    run_backtest,
    sync_etf_pool_to_db,
    sync_trading_calendar_to_db,
)
from vela_core.database import create_engine_from_url, create_session_factory, managed_session
from vela_core.models import (
    BacktestEquityCurve,
    DataFetchLog,
    ETFInfo,
    MarketPrice,
    StrategySignal,
)

from tests.integration_data import (
    ControlledMarketDataProvider,
    canonical_etf_pool,
    canonical_provider_prices,
    canonical_strategy_config,
    canonical_workflow_sessions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_canonical_ingestion_to_quant_pipeline_contract(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'core-pipeline.db'}"
    sessions = canonical_workflow_sessions()
    config = canonical_strategy_config()
    pool = canonical_etf_pool()
    provider = ControlledMarketDataProvider(canonical_provider_prices(sessions))
    fake_akshare = ModuleType("akshare")
    fake_akshare.tool_trade_date_hist_sina = lambda: pd.DataFrame(
        {"trade_date": [session.isoformat() for session in sessions]}
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    run_alembic_upgrade(database_url, REPO_ROOT / "alembic")
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine, expire_on_commit=False)

    with managed_session(session_factory) as session:
        pool_result = sync_etf_pool_to_db(session, pool)
        assert pool_result.inserted_count == len(pool.etfs)

    with managed_session(session_factory) as session:
        calendar_result = sync_trading_calendar_to_db(session)
        assert calendar_result.status == "success"
        assert calendar_result.synced_count == len(sessions)

    with managed_session(session_factory) as session:
        fetch_result = fetch_full_market_prices(session, provider=provider)
        assert fetch_result.status == "success"
        assert fetch_result.rows_inserted == len(sessions) * len(pool.etfs)

    with session_factory() as session:
        active_etfs = list(session.scalars(select(ETFInfo).where(ETFInfo.is_active.is_(True))))
        stored_sessions = list(session.scalars(select(MarketPrice.trade_date).distinct()))
        factor_price = session.scalar(
            select(MarketPrice).join(ETFInfo).where(ETFInfo.symbol == "159915")
        )
        fetch_log = session.scalar(select(DataFetchLog))

    assert {etf.symbol for etf in active_etfs} == {etf.symbol for etf in pool.etfs}
    assert set(stored_sessions) == set(sessions)
    assert factor_price is not None
    assert str(factor_price.close_price) == "100.000000"
    assert factor_price.factor_hfq == Decimal("1.234567000000")
    assert fetch_log is not None
    assert fetch_log.status == "success"
    assert provider.requests == [
        ("159915", None, None),
        ("510300", None, None),
        ("511010", None, None),
    ]

    with managed_session(session_factory) as session:
        manual = generate_and_persist_strategy_signal(
            session, config=config, signal_date=sessions[-1]
        )
        assert manual.status == "success"
        assert [position.rank for position in manual.positions] == [1]
        assert [position.symbol for position in manual.positions] == ["510300"]
        assert [position.target_weight for position in manual.positions] == [Decimal("1")]

    start_date = sessions[65]
    end_date = sessions[-1]
    with managed_session(session_factory) as session:
        first = run_backtest(
            session,
            config=config,
            start_date=start_date,
            end_date=end_date,
            started_at=datetime(2026, 7, 1, tzinfo=UTC),
        )
        assert first.status == "success"

    with session_factory() as session:
        first_run = get_backtest_result(session, run_id=first.backtest_run_id)
        manual_signal = session.get(StrategySignal, manual.strategy_signal_id)
        first_signal_ids = {
            signal.id
            for signal in session.scalars(
                select(StrategySignal).where(
                    StrategySignal.backtest_run_id == first.backtest_run_id
                )
            )
        }
        first_curve = list(
            session.scalars(
                select(BacktestEquityCurve)
                .where(BacktestEquityCurve.backtest_run_id == first.backtest_run_id)
                .order_by(BacktestEquityCurve.trade_date)
            )
        )

    assert first_run is not None
    assert manual_signal is not None
    assert manual_signal.source == "manual"
    assert manual_signal.backtest_run_id is None
    assert first_signal_ids
    assert first_signal_ids.isdisjoint({manual.strategy_signal_id})
    assert all(signal.source == "backtest" for signal in first_run.signals)
    assert first_run.data_snapshot_json is not None
    assert first_run.data_snapshot_json["data_checksum"]
    assert first_curve
    first_signals_before = [
        (
            signal.id,
            signal.signal_date,
            signal.source,
            signal.backtest_run_id,
            signal.status,
            signal.result,
        )
        for signal in first_run.signals
    ]
    non_empty_positions = [
        json.loads(row.positions_json) for row in first_curve if row.positions_json != "[]"
    ]
    assert non_empty_positions
    assert all(
        set(positions[0]) == {"etf_id", "target_weight", "actual_weight"}
        for positions in non_empty_positions
    )

    first_run_before = (
        first_run.total_return,
        first_run.annualized_return,
        first_run.max_drawdown,
        first_run.sharpe_ratio,
        first_run.volatility,
        first_run.data_snapshot_json,
        [(row.trade_date, row.net_value, row.positions_json) for row in first_curve],
    )
    with managed_session(session_factory) as session:
        second = run_backtest(
            session,
            config=config,
            start_date=start_date,
            end_date=end_date,
            started_at=datetime(2026, 7, 2, tzinfo=UTC),
        )
        assert second.status == "success"

    with session_factory() as session:
        first_after = get_backtest_result(session, run_id=first.backtest_run_id)
        second_run = get_backtest_result(session, run_id=second.backtest_run_id)
        second_signal_ids = {
            signal.id
            for signal in session.scalars(
                select(StrategySignal).where(
                    StrategySignal.backtest_run_id == second.backtest_run_id
                )
            )
        }
        dashboard = get_dashboard_summary(
            session,
            strategy_summary={"strategy_id": config.strategy_id, "version": config.version},
        )
        latest_successful = session.scalar(
            select(StrategySignal)
            .where(StrategySignal.strategy_id == config.strategy_id)
            .where(StrategySignal.config_version == config.version)
            .where(StrategySignal.status == "success")
            .order_by(StrategySignal.generated_at.desc(), StrategySignal.id.desc())
        )

    assert first_after is not None
    assert second_run is not None
    assert first_signal_ids.isdisjoint(second_signal_ids)
    assert [
        (
            signal.id,
            signal.signal_date,
            signal.source,
            signal.backtest_run_id,
            signal.status,
            signal.result,
        )
        for signal in first_after.signals
    ] == first_signals_before
    assert first_after.data_snapshot_json == second_run.data_snapshot_json
    assert (
        first_after.data_snapshot_json["data_checksum"]
        == second_run.data_snapshot_json["data_checksum"]
    )
    assert (
        first_after.total_return,
        first_after.annualized_return,
        first_after.max_drawdown,
        first_after.sharpe_ratio,
        first_after.volatility,
        first_after.data_snapshot_json,
        [(row.trade_date, row.net_value, row.positions_json) for row in first_curve],
    ) == first_run_before
    assert latest_successful is not None
    assert dashboard["latest_signal"]["signal_id"] == latest_successful.id
    assert dashboard["recent_backtest"]["run_id"] == second.backtest_run_id
    assert dashboard["recent_fetch_logs"][0]["fetch_log_id"] == fetch_log.id

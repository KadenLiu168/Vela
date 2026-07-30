import json
from datetime import date

from sqlalchemy import inspect, select
from vela_core.models import BacktestEquityCurve, BacktestRun, ETFInfo, MarketPrice, StrategySignal

from tests.integration_data import (
    ControlledMarketDataProvider,
    daily_price,
    equity_curve_row,
    prepare_sqlite_database,
    prepare_workflow_database,
)


def test_prepare_sqlite_database_initializes_orm_tables(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'empty.db'}"
    session_factory = prepare_sqlite_database(database_url)

    table_names = set(inspect(session_factory.kw["bind"]).get_table_names())

    assert {"etf_info", "market_price", "strategy_signal", "backtest_run"} <= table_names


def test_prepare_workflow_database_seeds_minimal_persisted_data(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'workflow.db'}"
    dataset = prepare_workflow_database(database_url)
    session_factory = prepare_sqlite_database(database_url, reset=False)

    with session_factory() as session:
        assert session.scalar(select(ETFInfo).where(ETFInfo.id == dataset.first_etf_id)) is not None
        assert session.query(ETFInfo).count() == 3
        assert session.query(MarketPrice).count() >= 393
        assert session.scalar(select(StrategySignal).where(StrategySignal.id == dataset.signal_id))
        assert session.scalar(select(BacktestRun).where(BacktestRun.id == dataset.backtest_run_id))
        assert session.query(BacktestEquityCurve).count() == 2


def test_controlled_market_data_provider_records_complete_inclusive_request_bounds() -> None:
    start_date = date(2026, 6, 2)
    end_date = date(2026, 6, 3)
    provider = ControlledMarketDataProvider(
        {
            "510300": [
                daily_price("510300", trade_date=date(2026, 6, 1)),
                daily_price("510300", trade_date=start_date),
                daily_price("510300", trade_date=end_date),
                daily_price("510300", trade_date=date(2026, 6, 4)),
            ]
        }
    )

    rows = provider.get_etf_daily_prices("510300", start_date=start_date, end_date=end_date)

    assert provider.requests == [("510300", start_date, end_date)]
    assert [row.trade_date for row in rows] == [start_date, end_date]


def test_shared_equity_curve_fixture_uses_production_position_schema() -> None:
    row = equity_curve_row(run_id=1, trade_date=date(2026, 6, 24), net_value=1)

    assert json.loads(row.positions_json) == [
        {"etf_id": 1, "target_weight": "1.000000", "actual_weight": "1.000000"}
    ]

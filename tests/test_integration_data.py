from sqlalchemy import inspect, select
from vela_core.models import BacktestEquityCurve, BacktestRun, ETFInfo, MarketPrice, StrategySignal

from tests.integration_data import prepare_sqlite_database, prepare_workflow_database


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

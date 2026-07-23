from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    DailyPrice,
    ETFConfig,
    ETFPoolConfig,
    run_local_setup_bootstrap,
)
from vela_core.app_config import AppConfig
from vela_core.models import ETFInfo, MarketPrice
from vela_core.strategy_config import (
    StrategyConfig,
    validate_strategy_config,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_SCRIPT_LOCATION = REPO_ROOT / "alembic"


def _make_strategy_config() -> StrategyConfig:
    return validate_strategy_config(
        {
            "strategy_id": "test_strategy",
            "version": "v1",
            "type": "dual_momentum",
            "universe_config": "test_pool.yaml",
            "parameters": {
                "momentum": {"short_window_days": 20, "long_window_days": 60},
                "score_weights": {"short": 0.4, "long": 0.6},
                "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                "selection": {"top_n": 2},
                "defense": {"assets": [{"exchange": "SSE", "symbol": "511010"}]},
            },
            "costs": {"transaction_cost_bps": 5},
            "performance": {"risk_free_rate": 0.03},
        }
    )


def _make_app_config() -> AppConfig:
    return AppConfig(
        strategy=_make_strategy_config(),
        etf_pool=_make_etf_pool_config(),
    )


def _make_etf_pool_config() -> ETFPoolConfig:
    return ETFPoolConfig(
        pool_id="test_pool",
        version=1,
        provider="test",
        currency="CNY",
        etfs=[
            ETFConfig(
                exchange="SSE",
                symbol="510300",
                name="沪深300ETF",
                category="equity_cn_large",
                is_active=True,
            ),
        ],
    )


def _create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine)


class RecordingProvider:
    name = "test"

    def __init__(self, prices):
        self._prices = prices
        self.requested_symbols: list[str] = []

    def get_etf_daily_prices(self, symbol, *, start_date=None, end_date=None):
        self.requested_symbols.append(symbol)
        return [p for p in self._prices if p.symbol == symbol]


class FailingProvider:
    name = "test"

    def get_etf_daily_prices(self, symbol, *, start_date=None, end_date=None):
        raise RuntimeError(f"provider failed for {symbol}")


def _daily_price(symbol="510300", trade_date=date(2026, 6, 18)):
    return DailyPrice(
        symbol=symbol,
        trade_date=trade_date,
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        factor=Decimal("1.0"),
        volume=1000,
    )


# 1.1 All three steps succeed
def test_bootstrap_all_steps_succeed(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap.db'}"
    session_factory = _create_session_factory(database_url)
    app_config = _make_app_config()
    provider = RecordingProvider([_daily_price()])

    with session_factory() as session:
        result = run_local_setup_bootstrap(
            session,
            provider=provider,
            app_config=app_config,
            database_url=database_url,
            script_location=ALEMBIC_SCRIPT_LOCATION,
        )
        session.commit()

    assert result.status == "success"
    assert result.failed_step is None
    assert len(result.steps) == 3
    assert [s.name for s in result.steps] == ["migrate", "sync_etf_pool", "fetch_full_market_data"]
    assert all(s.status == "success" for s in result.steps)
    assert result.total_duration_seconds > 0
    assert all(s.duration_seconds > 0 for s in result.steps)

    with session_factory() as session:
        etf = session.query(ETFInfo).filter_by(symbol="510300").one()
        assert etf.is_active is True
        prices = session.query(MarketPrice).all()
        assert len(prices) == 1


# 1.2 Step 2 (sync_etf_pool) failure aborts before step 3
def test_bootstrap_sync_etf_pool_failure_aborts(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap_sync_fail.db'}"
    session_factory = _create_session_factory(database_url)
    # Create AppConfig with an invalid ETF pool that will raise when sync is attempted
    # We monkey-patch sync_etf_pool_to_db to simulate failure
    provider = RecordingProvider([_daily_price()])

    import vela_core.bootstrap as bootstrap_mod

    original_sync = bootstrap_mod.sync_etf_pool_to_db

    def failing_sync(session, pool):
        raise RuntimeError("ETF pool config missing")

    bootstrap_mod.sync_etf_pool_to_db = failing_sync

    try:
        app_config = _make_app_config()
        with session_factory() as session:
            result = run_local_setup_bootstrap(
                session,
                provider=provider,
                app_config=app_config,
                database_url=database_url,
                script_location=ALEMBIC_SCRIPT_LOCATION,
            )
            session.commit()
    finally:
        bootstrap_mod.sync_etf_pool_to_db = original_sync

    assert result.status == "failed"
    assert result.failed_step == "sync_etf_pool"
    assert len(result.steps) == 2
    assert result.steps[0].name == "migrate"
    assert result.steps[0].status == "success"
    assert result.steps[1].name == "sync_etf_pool"
    assert result.steps[1].status == "failed"
    assert result.steps[1].error_message == "ETF pool config missing"
    assert provider.requested_symbols == []  # Step 3 never ran


# 1.3 Step 3 (fetch_full_market_data) failure still records earlier steps
def test_bootstrap_fetch_failure_records_earlier_steps(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap_fetch_fail.db'}"
    session_factory = _create_session_factory(database_url)
    app_config = _make_app_config()
    provider = FailingProvider()

    with session_factory() as session:
        result = run_local_setup_bootstrap(
            session,
            provider=provider,
            app_config=app_config,
            database_url=database_url,
            script_location=ALEMBIC_SCRIPT_LOCATION,
        )
        session.commit()

    assert result.status == "failed"
    assert result.failed_step == "fetch_full_market_data"
    assert len(result.steps) == 3
    assert result.steps[0].name == "migrate"
    assert result.steps[0].status == "success"
    assert result.steps[1].name == "sync_etf_pool"
    assert result.steps[1].status == "success"
    assert result.steps[2].name == "fetch_full_market_data"
    assert result.steps[2].status == "failed"
    assert "provider failed" in result.steps[2].error_message


# 1.4 Re-running against already-initialized database
def test_bootstrap_rerun_against_initialized_database(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap_rerun.db'}"
    session_factory = _create_session_factory(database_url)
    app_config = _make_app_config()
    provider = RecordingProvider([_daily_price()])

    # First run
    with session_factory() as session:
        result1 = run_local_setup_bootstrap(
            session,
            provider=provider,
            app_config=app_config,
            database_url=database_url,
            script_location=ALEMBIC_SCRIPT_LOCATION,
        )
        session.commit()

    assert result1.status == "success"

    # Second run
    with session_factory() as session:
        result2 = run_local_setup_bootstrap(
            session,
            provider=provider,
            app_config=app_config,
            database_url=database_url,
            script_location=ALEMBIC_SCRIPT_LOCATION,
        )
        session.commit()

    assert result2.status == "success"
    assert result2.steps[0].status == "success"  # Alembic re-run is no-op
    assert result2.steps[1].status == "success"  # ETF sync reports unchanged is still "success"
    assert result2.steps[2].status == "success"  # Market data fetch runs again


# 1.5 Per-step duration and total duration as floats
def test_bootstrap_result_durations_are_floats(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap_durations.db'}"
    session_factory = _create_session_factory(database_url)
    app_config = _make_app_config()
    provider = RecordingProvider([_daily_price()])

    with session_factory() as session:
        result = run_local_setup_bootstrap(
            session,
            provider=provider,
            app_config=app_config,
            database_url=database_url,
            script_location=ALEMBIC_SCRIPT_LOCATION,
        )
        session.commit()

    assert isinstance(result.total_duration_seconds, float)
    assert result.total_duration_seconds > 0
    for step in result.steps:
        assert isinstance(step.duration_seconds, float)
        assert step.duration_seconds > 0


# 1.6 run_local_setup_bootstrap requires script_location (no default)
def test_bootstrap_requires_script_location(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap_no_script.db'}"
    session_factory = _create_session_factory(database_url)
    app_config = _make_app_config()
    provider = RecordingProvider([_daily_price()])

    with session_factory() as session:
        with pytest.raises(TypeError, match="script_location"):
            run_local_setup_bootstrap(
                session,
                provider=provider,
                app_config=app_config,
                database_url=database_url,
            )

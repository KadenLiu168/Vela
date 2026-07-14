from datetime import date

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core import ETFConfig, ETFPoolConfig
from vela_core.app_config import AppConfig
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.strategy_config import (
    DefenseConfig,
    ETFIdentity,
    MomentumConfig,
    PerformanceConfig,
    ScoreWeightsConfig,
    SelectionConfig,
    StrategyConfig,
    TransactionCostsConfig,
    TrendFilterConfig,
)

from tests.integration_data import ControlledMarketDataProvider, daily_price


def _make_test_app_config() -> AppConfig:
    return AppConfig(
        strategy=StrategyConfig(
            strategy_id="test_strategy",
            version="v1",
            universe_config="test_pool.yaml",
            momentum=MomentumConfig(short_window_days=20, long_window_days=60),
            score_weights=ScoreWeightsConfig(short=0.4, long=0.6),
            trend_filter=TrendFilterConfig(moving_average_days=120, price_relation="above"),
            selection=SelectionConfig(top_n=2),
            defense=DefenseConfig(assets=[ETFIdentity(exchange="SSE", symbol="511010")]),
            costs=TransactionCostsConfig(transaction_cost_bps=5),
            performance=PerformanceConfig(risk_free_rate=0.03),
        ),
        etf_pool=ETFPoolConfig(
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
        ),
    )


# 3.1 Happy path: endpoint returns success aggregate
def test_bootstrap_endpoint_success(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap-api.db'}"
    provider = ControlledMarketDataProvider(
        {"510300": [daily_price(symbol="510300", trade_date=date(2026, 6, 18))]}
    )

    try:
        initialize_database(app, database_url=database_url)
        app.state.strategy_config = _make_test_app_config()
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/setup/bootstrap")
    finally:
        app.dependency_overrides.clear()
        app.state.strategy_config = None
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["failed_step"] is None
    assert len(body["steps"]) == 3
    assert [s["name"] for s in body["steps"]] == [
        "migrate",
        "sync_etf_pool",
        "fetch_full_market_data",
    ]
    assert all(s["status"] == "success" for s in body["steps"])
    assert body["total_duration_seconds"] > 0
    for step in body["steps"]:
        assert step["duration_seconds"] > 0


# 3.2 Step failure surfaces as status=failed with failed_step and error_message
def test_bootstrap_endpoint_step_failure(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap-api-fail.db'}"
    provider = ControlledMarketDataProvider({})

    try:
        initialize_database(app, database_url=database_url)
        app.state.strategy_config = _make_test_app_config()
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/setup/bootstrap")
    finally:
        app.dependency_overrides.clear()
        app.state.strategy_config = None
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["failed_step"] == "fetch_full_market_data"
    assert len(body["steps"]) == 3
    assert body["steps"][0]["status"] == "success"
    assert body["steps"][1]["status"] == "success"
    assert body["steps"][2]["status"] == "failed"
    assert body["steps"][2]["error_message"] is not None


# 3.3 Endpoint uses cached strategy config from app.state
def test_bootstrap_endpoint_uses_cached_config(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap-api-cached.db'}"
    provider = ControlledMarketDataProvider(
        {"510300": [daily_price(symbol="510300", trade_date=date(2026, 6, 18))]}
    )

    test_config = _make_test_app_config()

    try:
        initialize_database(app, database_url=database_url)
        app.state.strategy_config = test_config
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/setup/bootstrap")
    finally:
        app.dependency_overrides.clear()
        app.state.strategy_config = None
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["steps"][1]["status"] == "success"

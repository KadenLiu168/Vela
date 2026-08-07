import sys
from datetime import date
from types import ModuleType

import pandas as pd
from fastapi.testclient import TestClient
from vela_api.config import DEFAULT_STRATEGY_CONFIG_PATH
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core import BootstrapResult, ConfigError, ETFConfig, ETFPoolConfig
from vela_core.app_config import AppConfig
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.strategy_config import validate_strategy_config

from tests.integration_data import ControlledMarketDataProvider, daily_price


def _patch_akshare(monkeypatch) -> None:
    """Mock the akshare module so the bootstrap calendar step succeeds."""
    fake_akshare = ModuleType("akshare")
    fake_akshare.tool_trade_date_hist_sina = lambda: pd.DataFrame(
        {"trade_date": ["2026-06-01", "2026-06-02"]}
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)


def _make_test_app_config() -> AppConfig:
    return AppConfig(
        strategy=validate_strategy_config(
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
def test_bootstrap_endpoint_success(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap-api.db'}"
    provider = ControlledMarketDataProvider(
        {"510300": [daily_price(symbol="510300", trade_date=date(2026, 6, 18))]}
    )
    _patch_akshare(monkeypatch)

    try:
        initialize_database(app, database_url=database_url)
        monkeypatch.setattr(
            "vela_api.market_router.load_app_config", lambda _path: _make_test_app_config()
        )
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/setup/bootstrap")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["failed_step"] is None
    assert len(body["steps"]) == 4
    assert [s["name"] for s in body["steps"]] == [
        "migrate",
        "sync_etf_pool",
        "sync_trading_calendar",
        "fetch_full_market_data",
    ]
    assert all(s["status"] == "success" for s in body["steps"])
    assert body["total_duration_seconds"] > 0
    for step in body["steps"]:
        assert step["duration_seconds"] > 0


# 3.2 Step failure surfaces as status=failed with failed_step and error_message
def test_bootstrap_endpoint_step_failure(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap-api-fail.db'}"
    provider = ControlledMarketDataProvider({})
    _patch_akshare(monkeypatch)

    try:
        initialize_database(app, database_url=database_url)
        monkeypatch.setattr(
            "vela_api.market_router.load_app_config", lambda _path: _make_test_app_config()
        )
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/setup/bootstrap")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["failed_step"] == "fetch_full_market_data"
    assert len(body["steps"]) == 4
    assert body["steps"][0]["status"] == "success"
    assert body["steps"][1]["status"] == "success"
    assert body["steps"][2]["status"] == "success"
    assert body["steps"][3]["status"] == "failed"
    assert body["steps"][3]["error_message"] is not None


def test_bootstrap_endpoint_loads_config_per_request(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'bootstrap-api-reload.db'}"
    first_config = _make_test_app_config()
    second_config = _make_test_app_config().model_copy(
        update={"strategy": _make_test_app_config().strategy.model_copy(update={"version": "v2"})}
    )
    loaded_paths = []
    received_configs = []
    configs = iter([first_config, second_config])

    def load_config(path):
        loaded_paths.append(path)
        return next(configs)

    def record_bootstrap(session, *, provider, app_config, database_url, script_location):
        received_configs.append(app_config)
        return BootstrapResult(status="success")

    monkeypatch.setattr("vela_api.market_router.load_app_config", load_config)
    monkeypatch.setattr("vela_api.market_router.run_local_setup_bootstrap", record_bootstrap)

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)
        first_response = client.post("/api/setup/bootstrap")
        second_response = client.post("/api/setup/bootstrap")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert loaded_paths == [DEFAULT_STRATEGY_CONFIG_PATH, DEFAULT_STRATEGY_CONFIG_PATH]
    assert received_configs == [first_config, second_config]


def test_bootstrap_endpoint_returns_config_error_before_orchestration(monkeypatch) -> None:
    bootstrap_calls = []

    def raise_config_error(path):
        raise ConfigError("Failed to read configuration file config/missing.yaml", path=path)

    def record_bootstrap(*args, **kwargs):
        bootstrap_calls.append((args, kwargs))
        return BootstrapResult(status="success")

    monkeypatch.setattr("vela_api.market_router.load_app_config", raise_config_error)
    monkeypatch.setattr("vela_api.market_router.run_local_setup_bootstrap", record_bootstrap)

    response = TestClient(app, raise_server_exceptions=False).post("/api/setup/bootstrap")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "config_error"
    assert response.json()["error"]["category"] == "operation_failed"
    assert bootstrap_calls == []

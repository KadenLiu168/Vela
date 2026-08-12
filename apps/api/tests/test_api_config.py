from pathlib import Path

import pytest
import vela_api.config as api_config
import vela_api.system_router as system_router
from fastapi.testclient import TestClient
from vela_api.main import app
from vela_core import load_app_config
from vela_core.strategy_config import validate_strategy_config

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_config_endpoint_returns_strategy_and_etf_pool_summary() -> None:
    response = TestClient(app).get("/api/config")

    assert response.status_code == 200
    body = response.json()

    app_config = load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml")
    strategy = app_config.strategy
    etf_pool = app_config.etf_pool

    assert body["strategy"] == {
        "strategy_id": strategy.strategy_id,
        "version": strategy.version,
        "type": strategy.type,
        "universe_config": strategy.universe_config,
        "parameters": strategy.parameters.model_dump(),
        "costs": strategy.costs.model_dump(),
        "performance": strategy.performance.model_dump(),
        "rebalance": strategy.rebalance.model_dump(),
    }
    assert body["etf_pool"] == {
        "pool_id": etf_pool.pool_id,
        "version": etf_pool.version,
        "description": etf_pool.description,
        "provider": etf_pool.provider,
        "currency": etf_pool.currency,
        "total_etfs": len(etf_pool.etfs),
        "active_etfs": sum(1 for etf in etf_pool.etfs if etf.is_active),
        "etfs": [etf.model_dump(mode="json") for etf in etf_pool.etfs],
    }


def test_config_and_dashboard_endpoints_serialize_equal_weight_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_config = load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml").model_copy(
        update={
            "strategy": validate_strategy_config(
                {
                    "strategy_id": "equal_weight_test",
                    "version": "v2",
                    "type": "equal_weight",
                    "universe_config": "config/etf_pool.yaml",
                    "parameters": {},
                    "costs": {"transaction_cost_bps": 0},
                    "performance": {"risk_free_rate": 0},
                }
            )
        }
    )
    summary = api_config._serialize_config(app_config)
    monkeypatch.setattr(system_router, "get_config_summary", lambda _config: summary)
    monkeypatch.setattr(
        system_router,
        "get_dashboard_summary",
        lambda session, *, strategy_summary: {
            "strategy": strategy_summary,
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
        },
    )

    config_response = TestClient(app).get("/api/config")
    dashboard_response = TestClient(app).get("/api/dashboard")

    for response in (config_response, dashboard_response):
        assert response.status_code == 200
        assert response.json()["strategy"] == {
            "strategy_id": "equal_weight_test",
            "version": "v2",
            "type": "equal_weight",
            "universe_config": "config/etf_pool.yaml",
            "parameters": {},
            "costs": {"transaction_cost_bps": 0.0},
            "performance": {"risk_free_rate": 0.0},
            "rebalance": {"frequency": "weekly"},
        }

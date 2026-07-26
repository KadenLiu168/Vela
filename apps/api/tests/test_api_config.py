from pathlib import Path

import pytest
import vela_api.config as api_config
import vela_api.main as api_main
from fastapi.testclient import TestClient
from vela_api.main import app
from vela_core import load_app_config, load_etf_pool_config
from vela_core.strategy_config import validate_strategy_config

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_config_endpoint_returns_strategy_and_etf_pool_summary() -> None:
    response = TestClient(app).get("/api/config")

    assert response.status_code == 200
    body = response.json()

    app_config = load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml")
    etf_pool_config = load_etf_pool_config(REPO_ROOT / "config" / "etf_pool.yaml")
    expected_active = sum(1 for etf in etf_pool_config.etfs if etf.is_active)

    assert body["strategy"] == {
        "strategy_id": app_config.strategy.strategy_id,
        "version": "v1",
        "type": "dual_momentum",
        "universe_config": "config/etf_pool.yaml",
        "parameters": {
            "momentum": {"short_window_days": 63, "long_window_days": 126},
            "score_weights": {"short": 0.4, "long": 0.6},
            "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
            "selection": {"top_n": 2},
            "defense": {
                "assets": [
                    {"exchange": "SSE", "symbol": "511010"},
                    {"exchange": "SSE", "symbol": "511880"},
                    {"exchange": "SSE", "symbol": "518880"},
                ]
            },
        },
        "costs": {"transaction_cost_bps": 10.0},
        "performance": {"risk_free_rate": 0.02},
        "rebalance": {"frequency": "weekly"},
    }
    assert body["etf_pool"]["pool_id"] == "phase1_core"
    assert body["etf_pool"]["version"] == 1
    assert body["etf_pool"]["provider"] == "tencent"
    assert body["etf_pool"]["currency"] == "CNY"
    assert body["etf_pool"]["total_etfs"] == len(etf_pool_config.etfs)
    assert body["etf_pool"]["active_etfs"] == expected_active
    assert {
        "exchange": "SSE",
        "symbol": "511010",
        "name": "国债ETF",
        "category": "bond_cn",
        "is_active": True,
    } in body["etf_pool"]["etfs"]


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
    monkeypatch.setattr(api_main, "get_config_summary", lambda: summary)
    monkeypatch.setattr(
        api_main,
        "get_dashboard_summary",
        lambda session, *, strategy_summary: {
            "strategy": strategy_summary,
            "market_data": {},
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

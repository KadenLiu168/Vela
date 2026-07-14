from pathlib import Path

from fastapi.testclient import TestClient
from vela_api.main import app
from vela_core import load_app_config, load_etf_pool_config

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
        "universe_config": "config/etf_pool.yaml",
        "momentum": {"short_window_days": 63, "long_window_days": 126},
        "score_weights": {"short": 0.4, "long": 0.6},
        "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
        "selection": {"top_n": 2},
        "defense": {
            "assets": [
                {"exchange": "SSE", "symbol": "511010"},
                {"exchange": "SSE", "symbol": "511880"},
                {"exchange": "SSE", "symbol": "518880"},
            ],
        },
        "costs": {"transaction_cost_bps": 5.0},
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

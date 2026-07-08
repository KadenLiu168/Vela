from pathlib import Path
from typing import Any

from vela_core import AppConfig, load_app_config

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_STRATEGY_CONFIG_PATH = ROOT / "config" / "strategy_v1.yaml"
DEFAULT_ALEMBIC_SCRIPT_LOCATION = ROOT / "alembic"


def get_config_summary(config_path: Path = DEFAULT_STRATEGY_CONFIG_PATH) -> dict[str, Any]:
    config = load_app_config(config_path)
    return _serialize_config(config)


def _serialize_config(config: AppConfig) -> dict[str, Any]:
    active_etfs = [etf for etf in config.etf_pool.etfs if etf.is_active]
    return {
        "strategy": {
            "strategy_id": config.strategy.strategy_id,
            "version": config.strategy.version,
            "universe_config": config.strategy.universe_config,
            "momentum": config.strategy.momentum.model_dump(),
            "score_weights": config.strategy.score_weights.model_dump(),
            "trend_filter": config.strategy.trend_filter.model_dump(),
            "selection": config.strategy.selection.model_dump(),
            "defense": config.strategy.defense.model_dump(),
            "costs": config.strategy.costs.model_dump(),
            "performance": config.strategy.performance.model_dump(),
            "rebalance": config.strategy.rebalance.model_dump(),
        },
        "etf_pool": {
            "pool_id": config.etf_pool.pool_id,
            "version": config.etf_pool.version,
            "description": config.etf_pool.description,
            "provider": config.etf_pool.provider,
            "currency": config.etf_pool.currency,
            "total_etfs": len(config.etf_pool.etfs),
            "active_etfs": len(active_etfs),
            "etfs": [etf.model_dump() for etf in config.etf_pool.etfs],
        },
    }

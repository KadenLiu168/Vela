from pathlib import Path

from pydantic import BaseModel, ConfigDict

from vela_core.config import ETFPoolConfig, load_etf_pool_config
from vela_core.strategy_config import StrategyConfig, load_strategy_config


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy: StrategyConfig
    etf_pool: ETFPoolConfig


def load_app_config(strategy_config_path: str | Path) -> AppConfig:
    config_path = Path(strategy_config_path)
    strategy = load_strategy_config(config_path)
    etf_pool_path = _resolve_universe_config_path(config_path, strategy.universe_config)
    etf_pool = load_etf_pool_config(etf_pool_path)
    return AppConfig(strategy=strategy, etf_pool=etf_pool)


def _resolve_universe_config_path(strategy_config_path: Path, universe_config: str) -> Path:
    universe_path = Path(universe_config)
    if universe_path.is_absolute() or universe_path.exists():
        return universe_path
    return strategy_config_path.parent / universe_path

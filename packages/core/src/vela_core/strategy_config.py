from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from vela_core.config import (
    ConfigError,
    ETFPoolConfig,
    load_etf_pool_config,
    load_yaml_config,
)


class ETFIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    exchange: str = Field(min_length=1)
    symbol: str = Field(min_length=1)


class MomentumConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_window_days: int = Field(gt=0)
    long_window_days: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_window_order(self) -> "MomentumConfig":
        if self.short_window_days >= self.long_window_days:
            raise ValueError("short momentum window must be shorter than long momentum window")
        return self


class ScoreWeightsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    short: float = Field(gt=0)
    long: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_total_weight(self) -> "ScoreWeightsConfig":
        total_weight = self.short + self.long
        if abs(total_weight - 1.0) > 1e-9:
            raise ValueError("score weights must sum to 1.0")
        return self


class SelectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    top_n: int = Field(gt=0)


class DefenseConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    asset: ETFIdentity


class TransactionCostsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    transaction_cost_bps: float = Field(ge=0)


class StrategyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy_id: str = Field(min_length=1)
    version: Literal["v1"]
    universe_config: str = Field(min_length=1)
    momentum: MomentumConfig
    score_weights: ScoreWeightsConfig
    selection: SelectionConfig
    defense: DefenseConfig
    costs: TransactionCostsConfig


def load_strategy_config(path: str | Path) -> StrategyConfig:
    config_path = Path(path)
    config = load_yaml_config(config_path, StrategyConfig)
    universe_path = _resolve_universe_config_path(config_path, config.universe_config)
    universe = load_etf_pool_config(universe_path)
    _validate_defensive_asset(config, universe, universe_path, config_path)
    return config


def _resolve_universe_config_path(strategy_path: Path, universe_config: str) -> Path:
    universe_path = Path(universe_config)
    if universe_path.is_absolute() or universe_path.exists():
        return universe_path
    return strategy_path.parent / universe_path


def _validate_defensive_asset(
    config: StrategyConfig,
    universe: ETFPoolConfig,
    universe_path: Path,
    strategy_path: Path,
) -> None:
    asset = config.defense.asset
    is_active_universe_asset = any(
        etf.exchange == asset.exchange and etf.symbol == asset.symbol and etf.is_active
        for etf in universe.etfs
    )
    if not is_active_universe_asset:
        raise ConfigError(
            "Failed to validate configuration file "
            f"{strategy_path}: defense.asset {asset.exchange} {asset.symbol} "
            f"must exist as an active ETF in universe_config {universe_path}",
            path=strategy_path,
        )

from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from vela_core.config import (
    ConfigError,
    ETFPoolConfig,
    _format_validation_error,
    _load_yaml,
    load_etf_pool_config,
)
from vela_core.rebalance_dates import RebalanceFrequency


class ETFIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    exchange: str = Field(min_length=1)
    symbol: str = Field(min_length=1)


class RebalanceConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    frequency: RebalanceFrequency = "weekly"


class MomentumConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    short_window_days: int = Field(gt=0)
    long_window_days: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_window_order(self) -> "MomentumConfig":
        if self.short_window_days >= self.long_window_days:
            raise ValueError("short momentum window must be shorter than long momentum window")
        return self


class ScoreWeightsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    short: float = Field(gt=0)
    long: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_total_weight(self) -> "ScoreWeightsConfig":
        if abs(self.short + self.long - 1.0) > 1e-9:
            raise ValueError("score weights must sum to 1.0")
        return self


class TrendFilterConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    moving_average_days: Literal[60, 120, 250]
    price_relation: Literal["above", "below"]


class SelectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    top_n: int = Field(gt=0)


class DefenseConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    assets: list[ETFIdentity] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_defensive_assets(self) -> "DefenseConfig":
        seen: set[tuple[str, str]] = set()
        for asset in self.assets:
            key = (asset.exchange, asset.symbol)
            if key in seen:
                raise ValueError(
                    "defense.assets must not contain duplicate "
                    f"(exchange, symbol) entries: {asset.exchange} {asset.symbol}"
                )
            seen.add(key)
        return self


class TransactionCostsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    transaction_cost_bps: float = Field(ge=0)


class PerformanceConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    risk_free_rate: float = Field(ge=0)


class DualMomentumParams(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    momentum: MomentumConfig
    score_weights: ScoreWeightsConfig
    trend_filter: TrendFilterConfig
    selection: SelectionConfig
    defense: DefenseConfig


class EqualWeightParams(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BaseStrategyConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    universe_config: str = Field(min_length=1)
    rebalance: RebalanceConfig = Field(default_factory=RebalanceConfig)
    costs: TransactionCostsConfig
    performance: PerformanceConfig


class DualMomentumStrategyConfig(BaseStrategyConfig):
    type: Literal["dual_momentum"]
    parameters: DualMomentumParams

    @property
    def momentum(self) -> MomentumConfig:
        return self.parameters.momentum

    @property
    def score_weights(self) -> ScoreWeightsConfig:
        return self.parameters.score_weights

    @property
    def trend_filter(self) -> TrendFilterConfig:
        return self.parameters.trend_filter

    @property
    def selection(self) -> SelectionConfig:
        return self.parameters.selection

    @property
    def defense(self) -> DefenseConfig:
        return self.parameters.defense


class EqualWeightStrategyConfig(BaseStrategyConfig):
    type: Literal["equal_weight"]
    parameters: EqualWeightParams


StrategyConfig: TypeAlias = Annotated[
    DualMomentumStrategyConfig | EqualWeightStrategyConfig,
    Field(discriminator="type"),
]
STRATEGY_CONFIG_ADAPTER: TypeAdapter[StrategyConfig] = TypeAdapter(StrategyConfig)


def validate_strategy_config(data: Any) -> StrategyConfig:
    return STRATEGY_CONFIG_ADAPTER.validate_python(data)


def load_strategy_config(path: str | Path) -> StrategyConfig:
    config_path = Path(path)
    data = _load_yaml(config_path)
    if isinstance(data, dict) and "momentum" in data and "type" not in data:
        raise ConfigError(
            "Failed to validate configuration file "
            f"{config_path}: legacy flat strategy config; use type + parameters as in "
            "config/strategy_v1.yaml",
            path=config_path,
        )
    try:
        config = validate_strategy_config(data)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(config_path, exc), path=config_path) from exc
    if isinstance(config, DualMomentumStrategyConfig):
        universe_path = _resolve_universe_config_path(config_path, config.universe_config)
        _validate_defensive_assets(
            config, load_etf_pool_config(universe_path), universe_path, config_path
        )
    return config


def _resolve_universe_config_path(strategy_path: Path, universe_config: str) -> Path:
    universe_path = Path(universe_config)
    if universe_path.is_absolute() or universe_path.exists():
        return universe_path
    return strategy_path.parent / universe_path


def _validate_defensive_assets(
    config: DualMomentumStrategyConfig,
    universe: ETFPoolConfig,
    universe_path: Path,
    strategy_path: Path,
) -> None:
    for index, asset in enumerate(config.parameters.defense.assets):
        if not any(
            etf.exchange == asset.exchange and etf.symbol == asset.symbol and etf.is_active
            for etf in universe.etfs
        ):
            raise ConfigError(
                "Failed to validate configuration file "
                f"{strategy_path}: parameters.defense.assets[{index}] {asset.exchange} "
                f"{asset.symbol} must exist as an active ETF in universe_config {universe_path}",
                path=strategy_path,
            )

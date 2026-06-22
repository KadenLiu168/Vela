from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ETFIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    exchange: str = Field(min_length=1)
    symbol: str = Field(min_length=1)


class MomentumConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_window_days: int = Field(gt=0)
    long_window_days: int = Field(gt=0)


class ScoreWeightsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    short: float = Field(ge=0)
    long: float = Field(ge=0)

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
    raw_config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw_config, dict):
        raise ValueError("strategy config must be a YAML mapping")
    return StrategyConfig.model_validate(raw_config)

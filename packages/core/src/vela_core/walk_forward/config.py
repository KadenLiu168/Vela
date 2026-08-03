from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from vela_core.config import ConfigError, _format_validation_error, _load_yaml


class _ParameterBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)


class IntRangeParameter(_ParameterBase):
    type: Literal["int_range"]
    low: int
    high: int
    step: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> IntRangeParameter:
        if self.low > self.high:
            raise ValueError("low must be less than or equal to high")
        return self


class FloatRangeParameter(_ParameterBase):
    type: Literal["float_range"]
    low: float
    high: float
    step: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> FloatRangeParameter:
        if self.low > self.high:
            raise ValueError("low must be less than or equal to high")
        return self


class ChoiceParameter(_ParameterBase):
    type: Literal["choice"]
    values: list[int | float | str] = Field(min_length=1)


ParameterSpec: TypeAlias = Annotated[
    IntRangeParameter | FloatRangeParameter | ChoiceParameter,
    Field(discriminator="type"),
]
PARAMETER_SPEC_ADAPTER: TypeAdapter[ParameterSpec] = TypeAdapter(ParameterSpec)


class StrategySource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    base_config: Path


class WindowConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scheme: Literal["anchored_rolling"]
    start_date: date
    end_date: date
    train_years: int = Field(gt=0)
    test_years: int = Field(gt=0)
    step_years: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_date_order(self) -> WindowConfig:
        if self.start_date > self.end_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class WalkForwardConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: StrategySource
    window: WindowConfig
    objective: Literal["sharpe_ratio"]
    parameter_space: list[ParameterSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_parameter_names(self) -> WalkForwardConfig:
        names = [item.name for item in self.parameter_space]
        if len(names) != len(set(names)):
            raise ValueError("duplicate parameter name")
        return self


def load_walk_forward_config(path: str | Path) -> WalkForwardConfig:
    config_path = Path(path)
    data = _load_yaml(config_path)
    try:
        config = WalkForwardConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(config_path, exc), path=config_path) from exc
    base_config = config.strategy.base_config
    if not base_config.is_absolute():
        config = config.model_copy(
            update={
                "strategy": config.strategy.model_copy(
                    update={"base_config": config_path.parent / base_config}
                )
            }
        )
    return config

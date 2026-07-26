from __future__ import annotations

import copy
import itertools
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from pydantic import ValidationError

from vela_core.strategy_config import StrategyConfig, validate_strategy_config
from vela_core.walk_forward.config import (
    ChoiceParameter,
    IntRangeParameter,
    ParameterSpec,
)


@dataclass(frozen=True)
class StrategyConfigBuild:
    config: StrategyConfig | None
    skip_reason: str | None


def _values(spec: ParameterSpec) -> list[Any]:
    if isinstance(spec, ChoiceParameter):
        return spec.values
    if isinstance(spec, IntRangeParameter):
        return list(range(spec.low, spec.high + 1, spec.step))
    low, high, step = map(lambda value: Decimal(str(value)), (spec.low, spec.high, spec.step))
    values: list[Decimal] = []
    value = low
    while value <= high:
        values.append(value)
        value += step
    return values


def generate_combinations(parameter_specs: list[ParameterSpec]) -> list[dict[str, Any]]:
    return [
        dict(zip((item.name for item in parameter_specs), values, strict=True))
        for values in itertools.product(*(_values(item) for item in parameter_specs))
    ]


def merge_into_config(base_config_dict: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base_config_dict)
    for path, value in combo.items():
        target: dict[str, Any] = merged
        parts = path.split(".")
        for part in parts[:-1]:
            child = target.get(part)
            if not isinstance(child, dict):
                child = {}
                target[part] = child
            target = child
        target[parts[-1]] = value
    return merged


def build_strategy_config(
    base_config: dict[str, Any], combo: dict[str, Any]
) -> StrategyConfigBuild:
    try:
        return StrategyConfigBuild(
            validate_strategy_config(merge_into_config(base_config, combo)), None
        )
    except (ValidationError, ValueError, TypeError) as exc:
        return StrategyConfigBuild(None, str(exc))


def canonical_combination(combo: dict[str, Any]) -> str:
    return json.dumps(combo, sort_keys=True, default=str, separators=(",", ":"))

from collections.abc import Callable, Mapping
from types import MappingProxyType

from vela_core.strategies.dual_momentum import DualMomentumStrategy
from vela_core.strategies.equal_weight import EqualWeightStrategy
from vela_core.strategies.types import Strategy
from vela_core.strategy_config import (
    DualMomentumStrategyConfig,
    EqualWeightStrategyConfig,
    StrategyConfig,
)

StrategyFactory = Callable[[StrategyConfig], Strategy]


class StrategyRegistryError(ValueError):
    """The requested strategy cannot be resolved from the closed registry."""


def _dual_momentum_factory(config: StrategyConfig) -> Strategy:
    if not isinstance(config, DualMomentumStrategyConfig):
        raise ValueError("Strategy type dual_momentum has an invalid configuration variant")
    return DualMomentumStrategy(config.parameters)


def _equal_weight_factory(config: StrategyConfig) -> Strategy:
    if not isinstance(config, EqualWeightStrategyConfig):
        raise ValueError("Strategy type equal_weight has an invalid configuration variant")
    return EqualWeightStrategy(config.parameters)


_STRATEGY_FACTORIES: dict[str, StrategyFactory] = {
    "dual_momentum": _dual_momentum_factory,
    "equal_weight": _equal_weight_factory,
}
STRATEGY_FACTORIES: Mapping[str, StrategyFactory] = MappingProxyType(_STRATEGY_FACTORIES)


def resolve_strategy(config: StrategyConfig) -> Strategy:
    try:
        factory = STRATEGY_FACTORIES[config.type]
    except KeyError as exc:
        raise StrategyRegistryError(f"Unsupported strategy type: {config.type}") from exc
    return factory(config)

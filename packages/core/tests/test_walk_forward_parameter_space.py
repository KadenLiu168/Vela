from decimal import Decimal

from vela_core.walk_forward.config import PARAMETER_SPEC_ADAPTER
from vela_core.walk_forward.parameter_space import (
    build_strategy_config,
    generate_combinations,
    merge_into_config,
)


def test_generate_combinations_uses_decimal_ranges_and_cartesian_product() -> None:
    specs = [
        PARAMETER_SPEC_ADAPTER.validate_python(
            {
                "name": "parameters.alpha",
                "type": "float_range",
                "low": 0.2,
                "high": 0.6,
                "step": 0.1,
            }
        ),
        PARAMETER_SPEC_ADAPTER.validate_python(
            {"name": "parameters.beta", "type": "choice", "values": [1, 2]}
        ),
    ]

    combinations = generate_combinations(specs)

    assert len(combinations) == 10
    assert combinations[0] == {"parameters.alpha": Decimal("0.2"), "parameters.beta": 1}
    assert combinations[-1] == {"parameters.alpha": Decimal("0.6"), "parameters.beta": 2}


def test_merge_into_config_is_non_mutating_and_build_rejects_unknown_path() -> None:
    base = {"type": "dual_momentum", "parameters": {"selection": {"top_n": 2}}}
    merged = merge_into_config(base, {"parameters.selection.top_n": 1})
    assert merged["parameters"]["selection"]["top_n"] == 1
    assert base["parameters"]["selection"]["top_n"] == 2

    result = build_strategy_config(base, {"parameters.unknown": 1})
    assert result.config is None
    assert "unknown" in result.skip_reason

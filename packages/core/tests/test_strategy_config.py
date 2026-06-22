from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError
from vela_core import ConfigError
from vela_core.strategy_config import StrategyConfig, load_strategy_config

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_strategy_v1_config_loads_and_validates() -> None:
    config = load_strategy_config(REPO_ROOT / "config" / "strategy_v1.yaml")

    assert config.version == "v1"
    assert config.momentum.short_window_days == 63
    assert config.momentum.long_window_days == 126
    assert config.score_weights.short == 0.4
    assert config.score_weights.long == 0.6
    assert config.selection.top_n == 2
    assert config.defense.asset.exchange == "SSE"
    assert config.defense.asset.symbol == "511010"
    assert config.costs.transaction_cost_bps == 5


def test_strategy_config_loader_missing_file_raises_config_error(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "Failed to read configuration file" in message


def test_strategy_config_loader_yaml_parse_error_raises_config_error(tmp_path: Path) -> None:
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text("strategy_id: [unterminated\n", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "Failed to parse YAML" in message


def test_strategy_config_loader_missing_required_group_raises_config_error(
    tmp_path: Path,
) -> None:
    config = _valid_strategy_config()
    del config["momentum"]
    config_path = _write_strategy_config(tmp_path, config)

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "momentum" in message
    assert "Field required" in message


def test_strategy_config_loader_invalid_nested_field_raises_config_error(
    tmp_path: Path,
) -> None:
    config = _valid_strategy_config()
    config["momentum"]["short_window_days"] = 0
    config_path = _write_strategy_config(tmp_path, config)

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "momentum.short_window_days" in message


@pytest.mark.parametrize(
    "group",
    ["momentum", "score_weights", "selection", "defense", "costs"],
)
def test_strategy_config_rejects_missing_required_groups(group: str) -> None:
    config = _valid_strategy_config()
    del config[group]

    with pytest.raises(ValidationError):
        StrategyConfig.model_validate(config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("short_window_days", 0),
        ("long_window_days", 0),
    ],
)
def test_strategy_config_rejects_invalid_momentum_windows(field: str, value: int) -> None:
    config = _valid_strategy_config()
    config["momentum"][field] = value

    with pytest.raises(ValidationError):
        StrategyConfig.model_validate(config)


def test_strategy_config_rejects_invalid_score_weights() -> None:
    config = _valid_strategy_config()
    config["score_weights"]["short"] = 0.5
    config["score_weights"]["long"] = 0.6

    with pytest.raises(ValidationError):
        StrategyConfig.model_validate(config)


def test_strategy_config_rejects_invalid_top_n() -> None:
    config = _valid_strategy_config()
    config["selection"]["top_n"] = 0

    with pytest.raises(ValidationError):
        StrategyConfig.model_validate(config)


def test_strategy_config_rejects_negative_transaction_cost() -> None:
    config = _valid_strategy_config()
    config["costs"]["transaction_cost_bps"] = -1

    with pytest.raises(ValidationError):
        StrategyConfig.model_validate(config)


@pytest.mark.parametrize("field", ["exchange", "symbol"])
def test_strategy_config_requires_defensive_asset_identity_fields(field: str) -> None:
    config = _valid_strategy_config()
    del config["defense"]["asset"][field]

    with pytest.raises(ValidationError):
        StrategyConfig.model_validate(config)


def _valid_strategy_config() -> dict[str, Any]:
    return deepcopy(
        {
            "strategy_id": "dual_momentum",
            "version": "v1",
            "universe_config": "config/etf_pool.yaml",
            "momentum": {
                "short_window_days": 63,
                "long_window_days": 126,
            },
            "score_weights": {
                "short": 0.4,
                "long": 0.6,
            },
            "selection": {
                "top_n": 2,
            },
            "defense": {
                "asset": {
                    "exchange": "SSE",
                    "symbol": "511010",
                },
            },
            "costs": {
                "transaction_cost_bps": 5,
            },
        }
    )


def _write_strategy_config(tmp_path: Path, config: dict[str, Any]) -> Path:
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )
    return config_path

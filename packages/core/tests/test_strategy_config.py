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
    assert config.trend_filter.moving_average_days == 120
    assert config.trend_filter.price_relation == "above"
    assert config.selection.top_n == 2
    assert config.defense.asset.exchange == "SSE"
    assert config.defense.asset.symbol == "511010"
    assert config.costs.transaction_cost_bps == 5
    assert config.performance.risk_free_rate == 0.02
    assert config.rebalance.frequency == "weekly"


def test_strategy_config_accepts_valid_schema_input() -> None:
    config = StrategyConfig.model_validate(_valid_strategy_config())

    assert config.strategy_id == "dual_momentum"
    assert config.version == "v1"
    assert config.momentum.short_window_days == 63
    assert config.momentum.long_window_days == 126
    assert config.score_weights.short == 0.4
    assert config.score_weights.long == 0.6


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


def test_strategy_config_loader_rejects_defensive_asset_missing_from_universe(
    tmp_path: Path,
) -> None:
    pool_path = _write_etf_pool_config(
        tmp_path,
        [
            {
                "exchange": "SSE",
                "symbol": "510300",
                "name": "沪深300ETF",
                "is_active": True,
            },
        ],
    )
    config = _valid_strategy_config()
    config["universe_config"] = str(pool_path)
    config_path = _write_strategy_config(tmp_path, config)

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "defense.asset" in message
    assert "SSE 511010" in message
    assert str(pool_path) in message


def test_strategy_config_loader_rejects_inactive_defensive_asset(
    tmp_path: Path,
) -> None:
    pool_path = _write_etf_pool_config(
        tmp_path,
        [
            {
                "exchange": "SSE",
                "symbol": "511010",
                "name": "国债ETF",
                "is_active": False,
            },
        ],
    )
    config = _valid_strategy_config()
    config["universe_config"] = str(pool_path)
    config_path = _write_strategy_config(tmp_path, config)

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "defense.asset" in message
    assert "SSE 511010" in message
    assert str(pool_path) in message


def test_strategy_config_loader_accepts_active_defensive_asset(
    tmp_path: Path,
) -> None:
    pool_path = _write_etf_pool_config(
        tmp_path,
        [
            {
                "exchange": "SSE",
                "symbol": "511010",
                "name": "国债ETF",
                "is_active": True,
            },
        ],
    )
    config = _valid_strategy_config()
    config["universe_config"] = str(pool_path)
    config_path = _write_strategy_config(tmp_path, config)

    loaded_config = load_strategy_config(config_path)

    assert loaded_config.defense.asset.exchange == "SSE"
    assert loaded_config.defense.asset.symbol == "511010"


@pytest.mark.parametrize(
    "group",
    [
        "momentum",
        "score_weights",
        "trend_filter",
        "selection",
        "defense",
        "costs",
        "performance",
    ],
)
def test_strategy_config_rejects_missing_required_groups(group: str) -> None:
    config = _valid_strategy_config()
    del config[group]

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert group in message
    assert "Field required" in message


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

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert f"momentum.{field}" in message
    assert "greater than 0" in message


@pytest.mark.parametrize(
    ("short_window_days", "long_window_days"),
    [
        (126, 126),
        (252, 126),
    ],
)
def test_strategy_config_rejects_invalid_momentum_window_relationship(
    short_window_days: int,
    long_window_days: int,
) -> None:
    config = _valid_strategy_config()
    config["momentum"]["short_window_days"] = short_window_days
    config["momentum"]["long_window_days"] = long_window_days

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert "momentum" in message
    assert "short momentum window must be shorter than long momentum window" in message


def test_strategy_config_rejects_invalid_score_weights() -> None:
    config = _valid_strategy_config()
    config["score_weights"]["short"] = 0.5
    config["score_weights"]["long"] = 0.6

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert "score_weights" in message
    assert "score weights must sum to 1.0" in message


@pytest.mark.parametrize("field", ["short", "long"])
def test_strategy_config_rejects_zero_score_weights(field: str) -> None:
    config = _valid_strategy_config()
    config["score_weights"][field] = 0

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert f"score_weights.{field}" in message
    assert "greater than 0" in message


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("moving_average_days", 60),
        ("price_relation", "at_or_above"),
    ],
)
def test_strategy_config_rejects_unsupported_trend_filter(
    field: str,
    value: int | str,
) -> None:
    config = _valid_strategy_config()
    config["trend_filter"][field] = value

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert f"trend_filter.{field}" in message
    assert "Input should be" in message


def test_strategy_config_rejects_invalid_top_n() -> None:
    config = _valid_strategy_config()
    config["selection"]["top_n"] = 0

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert "selection.top_n" in message
    assert "greater than 0" in message


def test_strategy_config_rejects_negative_transaction_cost() -> None:
    config = _valid_strategy_config()
    config["costs"]["transaction_cost_bps"] = -1

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert "costs.transaction_cost_bps" in message
    assert "greater than or equal to 0" in message


def test_strategy_config_rejects_negative_risk_free_rate() -> None:
    config = _valid_strategy_config()
    config["performance"]["risk_free_rate"] = -0.01

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert "performance.risk_free_rate" in message
    assert "greater than or equal to 0" in message


def test_rebalance_config_defaults_to_weekly_when_omitted() -> None:
    config = _valid_strategy_config()

    validated = StrategyConfig.model_validate(config)

    assert validated.rebalance.frequency == "weekly"


def test_rebalance_config_accepts_weekly_frequency() -> None:
    config = _valid_strategy_config()
    config["rebalance"] = {"frequency": "weekly"}

    validated = StrategyConfig.model_validate(config)

    assert validated.rebalance.frequency == "weekly"


def test_rebalance_config_accepts_monthly_frequency() -> None:
    config = _valid_strategy_config()
    config["rebalance"] = {"frequency": "monthly"}

    validated = StrategyConfig.model_validate(config)

    assert validated.rebalance.frequency == "monthly"


def test_rebalance_config_rejects_unsupported_frequency() -> None:
    config = _valid_strategy_config()
    config["rebalance"] = {"frequency": "biweekly"}

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert "rebalance.frequency" in message


@pytest.mark.parametrize("field", ["exchange", "symbol"])
def test_strategy_config_requires_defensive_asset_identity_fields(field: str) -> None:
    config = _valid_strategy_config()
    del config["defense"]["asset"][field]

    with pytest.raises(ValidationError) as exc_info:
        StrategyConfig.model_validate(config)

    message = str(exc_info.value)
    assert f"defense.asset.{field}" in message
    assert "Field required" in message


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
            "trend_filter": {
                "moving_average_days": 120,
                "price_relation": "above",
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
            "performance": {
                "risk_free_rate": 0.02,
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


def _write_etf_pool_config(tmp_path: Path, etfs: list[dict[str, Any]]) -> Path:
    pool_path = tmp_path / "etf_pool.yaml"
    pool_path.write_text(
        yaml.safe_dump(
            {
                "pool_id": "test_pool",
                "version": 1,
                "provider": "akshare",
                "currency": "CNY",
                "etfs": etfs,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return pool_path

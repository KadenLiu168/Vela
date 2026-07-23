from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError
from vela_core import ConfigError, strategy_config
from vela_core.strategy_config import load_strategy_config, validate_strategy_config

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
    assert [(a.exchange, a.symbol) for a in config.defense.assets] == [
        ("SSE", "511010"),
        ("SSE", "511880"),
        ("SSE", "518880"),
    ]
    assert config.costs.transaction_cost_bps == 5
    assert config.performance.risk_free_rate == 0.02
    assert config.rebalance.frequency == "weekly"


def test_strategy_config_accepts_valid_schema_input() -> None:
    config = validate_strategy_config(_valid_strategy_config())

    assert config.strategy_id == "dual_momentum"
    assert config.version == "v1"
    assert config.momentum.short_window_days == 63
    assert config.momentum.long_window_days == 126
    assert config.score_weights.short == 0.4
    assert config.score_weights.long == 0.6


def test_strategy_config_adapter_accepts_equal_weight_with_empty_parameters() -> None:
    config = _valid_equal_weight_config()

    validated = strategy_config.validate_strategy_config(config)

    assert validated.type == "equal_weight"
    assert validated.parameters.model_dump() == {}


def test_strategy_config_adapter_rejects_legacy_fields_mixed_with_new_shape() -> None:
    config = _valid_strategy_config()
    dict.__setitem__(config, "momentum", {"short_window_days": 63, "long_window_days": 126})

    with pytest.raises(ValidationError) as exc_info:
        strategy_config.validate_strategy_config(config)

    assert "momentum" in str(exc_info.value)


def test_strategy_config_adapter_rejects_empty_version() -> None:
    config = _valid_equal_weight_config()
    config["version"] = ""

    with pytest.raises(ValidationError) as exc_info:
        strategy_config.validate_strategy_config(config)

    assert "version" in str(exc_info.value)


@pytest.mark.parametrize("field", ["type", "parameters"])
def test_strategy_config_adapter_requires_variant_fields(field: str) -> None:
    config = _valid_equal_weight_config()
    del config[field]

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    assert field in str(exc_info.value)


def test_strategy_config_adapter_rejects_unknown_type() -> None:
    config = _valid_equal_weight_config()
    config["type"] = "unsupported"

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    assert "unsupported" in str(exc_info.value)


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
    assert "defense.assets[0]" in message
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
    assert "defense.assets[0]" in message
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

    assert loaded_config.defense.assets[0].exchange == "SSE"
    assert loaded_config.defense.assets[0].symbol == "511010"


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
        validate_strategy_config(config)

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
        validate_strategy_config(config)

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
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "momentum" in message
    assert "short momentum window must be shorter than long momentum window" in message


def test_strategy_config_rejects_invalid_score_weights() -> None:
    config = _valid_strategy_config()
    config["score_weights"]["short"] = 0.5
    config["score_weights"]["long"] = 0.6

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "score_weights" in message
    assert "score weights must sum to 1.0" in message


@pytest.mark.parametrize("field", ["short", "long"])
def test_strategy_config_rejects_zero_score_weights(field: str) -> None:
    config = _valid_strategy_config()
    config["score_weights"][field] = 0

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert f"score_weights.{field}" in message
    assert "greater than 0" in message


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("moving_average_days", 30),
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
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert f"trend_filter.{field}" in message
    assert "Input should be" in message


@pytest.mark.parametrize(
    ("moving_average_days", "price_relation"),
    [
        (60, "above"),
        (60, "below"),
        (120, "above"),
        (120, "below"),
        (250, "above"),
        (250, "below"),
    ],
)
def test_strategy_config_accepts_supported_trend_filter_values(
    moving_average_days: int,
    price_relation: str,
) -> None:
    config = _valid_strategy_config()
    config["trend_filter"]["moving_average_days"] = moving_average_days
    config["trend_filter"]["price_relation"] = price_relation

    validated = validate_strategy_config(config)

    assert validated.trend_filter.moving_average_days == moving_average_days
    assert validated.trend_filter.price_relation == price_relation


def test_strategy_config_rejects_invalid_top_n() -> None:
    config = _valid_strategy_config()
    config["selection"]["top_n"] = 0

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "selection.top_n" in message
    assert "greater than 0" in message


def test_strategy_config_rejects_negative_transaction_cost() -> None:
    config = _valid_strategy_config()
    config["costs"]["transaction_cost_bps"] = -1

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "costs.transaction_cost_bps" in message
    assert "greater than or equal to 0" in message


def test_strategy_config_rejects_negative_risk_free_rate() -> None:
    config = _valid_strategy_config()
    config["performance"]["risk_free_rate"] = -0.01

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "performance.risk_free_rate" in message
    assert "greater than or equal to 0" in message


def test_rebalance_config_defaults_to_weekly_when_omitted() -> None:
    config = _valid_strategy_config()

    validated = validate_strategy_config(config)

    assert validated.rebalance.frequency == "weekly"


def test_rebalance_config_accepts_weekly_frequency() -> None:
    config = _valid_strategy_config()
    config["rebalance"] = {"frequency": "weekly"}

    validated = validate_strategy_config(config)

    assert validated.rebalance.frequency == "weekly"


def test_rebalance_config_accepts_monthly_frequency() -> None:
    config = _valid_strategy_config()
    config["rebalance"] = {"frequency": "monthly"}

    validated = validate_strategy_config(config)

    assert validated.rebalance.frequency == "monthly"


def test_rebalance_config_rejects_unsupported_frequency() -> None:
    config = _valid_strategy_config()
    config["rebalance"] = {"frequency": "biweekly"}

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "rebalance.frequency" in message


@pytest.mark.parametrize("field", ["exchange", "symbol"])
def test_strategy_config_requires_defensive_asset_identity_fields(field: str) -> None:
    config = _valid_strategy_config()
    del config["defense"]["assets"][0][field]

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "defense.assets" in message
    assert field in message
    assert "Field required" in message


def test_strategy_config_rejects_empty_defensive_assets_list() -> None:
    config = _valid_strategy_config()
    config["defense"]["assets"] = []

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "defense.assets" in message
    assert "at least 1" in message


def test_strategy_config_rejects_duplicate_defensive_assets() -> None:
    config = _valid_strategy_config()
    config["defense"]["assets"] = [
        {"exchange": "SSE", "symbol": "511010"},
        {"exchange": "SSE", "symbol": "511010"},
    ]

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(config)

    message = str(exc_info.value)
    assert "defense.assets" in message
    assert "duplicate" in message.lower()


def test_strategy_config_loader_names_specific_inactive_defensive_asset_by_index(
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
            {
                "exchange": "SSE",
                "symbol": "511880",
                "name": "银华日利ETF",
                "is_active": False,
            },
        ],
    )
    config = _valid_strategy_config()
    config["universe_config"] = str(pool_path)
    config["defense"]["assets"] = [
        {"exchange": "SSE", "symbol": "511010"},
        {"exchange": "SSE", "symbol": "511880"},
    ]
    config_path = _write_strategy_config(tmp_path, config)

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "defense.assets[1]" in message
    assert "SSE 511880" in message
    assert str(pool_path) in message


def _valid_strategy_config() -> dict[str, Any]:
    class _NestedConfig(dict[str, Any]):
        _parameter_fields = {"momentum", "score_weights", "trend_filter", "selection", "defense"}

        def __getitem__(self, key: str) -> Any:
            if key in self._parameter_fields:
                return super().__getitem__("parameters")[key]
            return super().__getitem__(key)

        def __delitem__(self, key: str) -> None:
            if key in self._parameter_fields:
                del super().__getitem__("parameters")[key]
                return
            super().__delitem__(key)

        def __setitem__(self, key: str, value: Any) -> None:
            if key in self._parameter_fields:
                super().__getitem__("parameters")[key] = value
                return
            super().__setitem__(key, value)

    return _NestedConfig(
        deepcopy(
            {
                "strategy_id": "dual_momentum",
                "version": "v1",
                "type": "dual_momentum",
                "universe_config": "config/etf_pool.yaml",
                "parameters": {
                    "momentum": {"short_window_days": 63, "long_window_days": 126},
                    "score_weights": {"short": 0.4, "long": 0.6},
                    "trend_filter": {"moving_average_days": 120, "price_relation": "above"},
                    "selection": {"top_n": 2},
                    "defense": {"assets": [{"exchange": "SSE", "symbol": "511010"}]},
                },
                "costs": {
                    "transaction_cost_bps": 5,
                },
                "performance": {
                    "risk_free_rate": 0.02,
                },
            }
        )
    )


def _valid_equal_weight_config() -> dict[str, Any]:
    return {
        "strategy_id": "equal_weight",
        "version": "v2",
        "type": "equal_weight",
        "universe_config": "config/etf_pool.yaml",
        "parameters": {},
        "costs": {"transaction_cost_bps": 5},
        "performance": {"risk_free_rate": 0.02},
    }


def _write_strategy_config(tmp_path: Path, config: dict[str, Any]) -> Path:
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text(
        yaml.safe_dump(dict(config), sort_keys=False),
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
                "provider": "tencent",
                "currency": "CNY",
                "etfs": etfs,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return pool_path

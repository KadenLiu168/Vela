from pathlib import Path

import pytest
from vela_core import (
    ConfigError,
    ETFPoolConfig,
    StrategyEnvelopeConfig,
    load_etf_pool_config,
    load_strategy_envelope_config,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_load_existing_etf_pool_yaml_returns_typed_config() -> None:
    config = load_etf_pool_config(REPO_ROOT / "config" / "etf_pool.yaml")

    assert isinstance(config, ETFPoolConfig)
    assert config.pool_id == "phase1_core"
    assert config.provider == "akshare"
    assert config.currency == "CNY"
    assert len(config.etfs) == 6
    assert config.etfs[0].exchange == "SSE"
    assert isinstance(config.etfs[0].exchange, str)


def test_etf_pool_rejects_duplicate_exchange_symbol(tmp_path: Path) -> None:
    config_path = tmp_path / "etf_pool.yaml"
    config_path.write_text(
        """
pool_id: test_pool
version: 1
provider: akshare
currency: CNY
etfs:
  - exchange: SSE
    symbol: "510300"
    name: First ETF
  - exchange: SSE
    symbol: "510300"
    name: Duplicate ETF
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_etf_pool_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "etfs" in message
    assert "duplicate ETF entry: SSE 510300" in message


def test_etf_pool_allows_same_symbol_on_different_exchanges(tmp_path: Path) -> None:
    config_path = tmp_path / "etf_pool.yaml"
    config_path.write_text(
        """
pool_id: test_pool
version: 1
provider: akshare
currency: CNY
etfs:
  - exchange: SSE
    symbol: "510300"
    name: SSE ETF
  - exchange: SZSE
    symbol: "510300"
    name: SZSE ETF
""",
        encoding="utf-8",
    )

    config = load_etf_pool_config(config_path)

    assert [(etf.exchange, etf.symbol) for etf in config.etfs] == [
        ("SSE", "510300"),
        ("SZSE", "510300"),
    ]


def test_load_strategy_envelope_yaml_returns_typed_config(tmp_path: Path) -> None:
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text(
        """
strategy_name: rotation
config_version: v1
universe_pool_id: phase1_core
parameters:
  lookback_days: 60
  rebalance_frequency: monthly
  risk_control:
    max_weight: 0.4
""",
        encoding="utf-8",
    )

    config = load_strategy_envelope_config(config_path)

    assert isinstance(config, StrategyEnvelopeConfig)
    assert config.strategy_name == "rotation"
    assert config.config_version == "v1"
    assert config.universe_pool_id == "phase1_core"
    assert config.parameters == {
        "lookback_days": 60,
        "rebalance_frequency": "monthly",
        "risk_control": {"max_weight": 0.4},
    }


def test_config_error_includes_validation_path(tmp_path: Path) -> None:
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text(
        """
strategy_name: rotation
config_version: v1
parameters: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_envelope_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "universe_pool_id" in message
    assert "Field required" in message


def test_config_error_includes_yaml_parse_context(tmp_path: Path) -> None:
    config_path = tmp_path / "strategy.yaml"
    config_path.write_text("strategy_name: [unterminated\n", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_strategy_envelope_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "Failed to parse YAML" in message


def test_config_error_includes_missing_file_path(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigError) as exc_info:
        load_etf_pool_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "Failed to read configuration file" in message

from pathlib import Path

import pytest
from vela_core import (
    AppConfig,
    ConfigError,
    ETFPoolConfig,
    load_app_config,
    load_etf_pool_config,
)
from vela_core.strategy_config import StrategyConfig

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


def test_etf_pool_config_error_includes_validation_path(tmp_path: Path) -> None:
    config_path = tmp_path / "etf_pool.yaml"
    config_path.write_text(
        """
version: 1
provider: akshare
currency: CNY
etfs:
  - exchange: SSE
    symbol: "510300"
    name: 沪深300ETF
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_etf_pool_config(config_path)

    message = str(exc_info.value)
    assert str(config_path) in message
    assert "pool_id" in message
    assert "Field required" in message


def test_etf_pool_config_error_includes_yaml_parse_context(tmp_path: Path) -> None:
    config_path = tmp_path / "etf_pool.yaml"
    config_path.write_text("pool_id: [unterminated\n", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_etf_pool_config(config_path)

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


def test_load_existing_app_config_returns_typed_config() -> None:
    config = load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml")

    assert isinstance(config, AppConfig)
    assert isinstance(config.strategy, StrategyConfig)
    assert isinstance(config.etf_pool, ETFPoolConfig)


def test_load_existing_app_config_contains_checked_in_values() -> None:
    config = load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml")

    assert config.strategy.version == "v1"
    assert config.strategy.universe_config == "config/etf_pool.yaml"
    assert config.etf_pool.pool_id == "phase1_core"
    assert config.etf_pool.provider == "akshare"
    assert len(config.etf_pool.etfs) == 6


def test_app_config_resolves_universe_config_from_working_directory() -> None:
    config = load_app_config(REPO_ROOT / "config" / "strategy_v1.yaml")

    assert config.etf_pool.pool_id == "phase1_core"


def test_app_config_resolves_universe_config_from_strategy_file_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    strategy_path = config_dir / "strategy.yaml"
    pool_path = config_dir / "etf_pool.yaml"
    strategy_path.write_text(
        """
strategy_id: dual_momentum
version: v1
universe_config: etf_pool.yaml
momentum:
  short_window_days: 63
  long_window_days: 126
score_weights:
  short: 0.4
  long: 0.6
selection:
  top_n: 2
defense:
  asset:
    exchange: SSE
    symbol: "511010"
costs:
  transaction_cost_bps: 5
""",
        encoding="utf-8",
    )
    pool_path.write_text(
        """
pool_id: local_pool
version: 1
provider: akshare
currency: CNY
etfs:
  - exchange: SSE
    symbol: "511010"
    name: 国债ETF
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = load_app_config(strategy_path)

    assert config.etf_pool.pool_id == "local_pool"


def test_app_config_missing_referenced_etf_pool_includes_pool_path(tmp_path: Path) -> None:
    strategy_path = tmp_path / "strategy.yaml"
    missing_pool_path = tmp_path / "missing_pool.yaml"
    strategy_path.write_text(
        f"""
strategy_id: dual_momentum
version: v1
universe_config: {missing_pool_path}
momentum:
  short_window_days: 63
  long_window_days: 126
score_weights:
  short: 0.4
  long: 0.6
selection:
  top_n: 2
defense:
  asset:
    exchange: SSE
    symbol: "511010"
costs:
  transaction_cost_bps: 5
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_app_config(strategy_path)

    message = str(exc_info.value)
    assert str(missing_pool_path) in message
    assert "Failed to read configuration file" in message


def test_app_config_invalid_referenced_etf_pool_includes_pool_path_and_field(
    tmp_path: Path,
) -> None:
    strategy_path = tmp_path / "strategy.yaml"
    pool_path = tmp_path / "etf_pool.yaml"
    strategy_path.write_text(
        f"""
strategy_id: dual_momentum
version: v1
universe_config: {pool_path}
momentum:
  short_window_days: 63
  long_window_days: 126
score_weights:
  short: 0.4
  long: 0.6
selection:
  top_n: 2
defense:
  asset:
    exchange: SSE
    symbol: "511010"
costs:
  transaction_cost_bps: 5
""",
        encoding="utf-8",
    )
    pool_path.write_text(
        """
version: 1
provider: akshare
currency: CNY
etfs:
  - exchange: SSE
    symbol: "511010"
    name: 国债ETF
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_app_config(strategy_path)

    message = str(exc_info.value)
    assert str(pool_path) in message
    assert "pool_id" in message

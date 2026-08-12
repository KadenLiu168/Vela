from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml
from vela_core import (
    AppConfig,
    ConfigError,
    ETFPoolConfig,
    ETFSessionStatusDocument,
    load_app_config,
    load_etf_pool_config,
    load_etf_session_status_document,
)
from vela_core.strategy_config import DualMomentumStrategyConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
ETF_POOL_PATH = REPO_ROOT / "config" / "etf_pool.yaml"
ETF_SESSION_STATUS_PATH = REPO_ROOT / "config" / "etf_session_status.yaml"
STRATEGY_PATH = REPO_ROOT / "config" / "strategy_v1.yaml"


def test_load_existing_etf_pool_yaml_returns_typed_config() -> None:
    config = load_etf_pool_config(ETF_POOL_PATH)
    raw_config = yaml.safe_load(ETF_POOL_PATH.read_text())

    assert isinstance(config, ETFPoolConfig)
    assert config.pool_id == raw_config["pool_id"]
    assert config.provider == raw_config["provider"]
    assert config.currency == raw_config["currency"]
    raw_etfs = raw_config["etfs"]
    assert len(config.etfs) == len(raw_etfs)
    assert config.etfs[0].exchange == raw_etfs[0]["exchange"]
    assert isinstance(config.etfs[0].exchange, str)


def test_reviewed_etf_pool_listing_dates_match_exchange_evidence() -> None:
    config = load_etf_pool_config(ETF_POOL_PATH)

    assert {
        (etf.exchange, etf.symbol): etf.listing_date.isoformat()
        for etf in config.etfs
        if etf.listing_date is not None
    } == {
        ("SSE", "510300"): "2012-05-28",
        ("SZSE", "159915"): "2011-12-09",
        ("SSE", "512100"): "2016-11-04",
        ("SSE", "588000"): "2020-11-16",
        ("SSE", "515080"): "2019-12-27",
        ("SSE", "513130"): "2021-06-01",
        ("SSE", "513100"): "2013-05-15",
        ("SSE", "513500"): "2014-01-15",
        ("SSE", "518880"): "2013-07-29",
        ("SSE", "511010"): "2013-03-25",
        ("SSE", "511880"): "2013-04-18",
    }


def test_load_reviewed_etf_session_status_yaml_is_exact_and_typed() -> None:
    config = load_etf_session_status_document(ETF_SESSION_STATUS_PATH)

    assert isinstance(config, ETFSessionStatusDocument)
    identities = [
        (entry.exchange, entry.symbol, entry.trade_date.isoformat()) for entry in config.entries
    ]
    assert identities == [
        ("SZSE", "159915", "2021-02-08"),
        ("SSE", "513100", "2022-01-13"),
        ("SSE", "513500", "2022-03-29"),
        ("SSE", "512100", "2022-09-02"),
    ]
    assert [entry.share_ratio for entry in config.entries] == [
        None,
        Decimal("5"),
        Decimal("2"),
        Decimal("0.36555"),
    ]
    assert [urlparse(entry.source_uri).hostname for entry in config.entries] == [
        "cdn.efunds.com.cn",
        "www.sse.com.cn",
        "www.sse.com.cn",
        "www.sse.com.cn",
    ]


def test_etf_pool_rejects_duplicate_exchange_symbol(tmp_path: Path) -> None:
    config_path = tmp_path / "etf_pool.yaml"
    config_path.write_text(
        """
pool_id: test_pool
version: 1
provider: tencent
currency: CNY
etfs:
  - exchange: SSE
    symbol: "510300"
    name: First ETF
    listing_date: 2020-01-01
  - exchange: SSE
    symbol: "510300"
    name: Duplicate ETF
    listing_date: 2020-01-01
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
provider: tencent
currency: CNY
etfs:
  - exchange: SSE
    symbol: "510300"
    name: SSE ETF
    listing_date: 2020-01-01
  - exchange: SZSE
    symbol: "510300"
    name: SZSE ETF
    listing_date: 2020-01-01
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
provider: tencent
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
    config = load_app_config(STRATEGY_PATH)

    assert isinstance(config, AppConfig)
    assert isinstance(config.strategy, DualMomentumStrategyConfig)
    assert isinstance(config.etf_pool, ETFPoolConfig)


def test_load_existing_app_config_contains_checked_in_values() -> None:
    config = load_app_config(STRATEGY_PATH)
    raw_strategy = yaml.safe_load(STRATEGY_PATH.read_text())
    raw_etf_pool = yaml.safe_load(ETF_POOL_PATH.read_text())

    assert config.strategy.version == raw_strategy["version"]
    assert config.strategy.universe_config == raw_strategy["universe_config"]
    assert config.etf_pool.pool_id == raw_etf_pool["pool_id"]
    assert config.etf_pool.provider == raw_etf_pool["provider"]
    assert len(config.etf_pool.etfs) == len(raw_etf_pool["etfs"])


def test_app_config_resolves_universe_config_from_working_directory() -> None:
    config = load_app_config(STRATEGY_PATH)
    raw_etf_pool = yaml.safe_load(ETF_POOL_PATH.read_text())

    assert config.etf_pool.pool_id == raw_etf_pool["pool_id"]


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
type: dual_momentum
universe_config: etf_pool.yaml
parameters:
  momentum:
    short_window_days: 63
    long_window_days: 126
  score_weights:
    short: 0.4
    long: 0.6
  trend_filter:
    moving_average_days: 120
    price_relation: above
  selection:
    top_n: 2
  defense:
    assets:
      - exchange: SSE
        symbol: "511010"
costs:
  transaction_cost_bps: 5
performance:
  risk_free_rate: 0.02
""",
        encoding="utf-8",
    )
    pool_path.write_text(
        """
pool_id: local_pool
version: 1
provider: tencent
currency: CNY
etfs:
  - exchange: SSE
    symbol: "511010"
    name: 国债ETF
    listing_date: 2020-01-01
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
type: dual_momentum
universe_config: {missing_pool_path}
parameters:
  momentum:
    short_window_days: 63
    long_window_days: 126
  score_weights:
    short: 0.4
    long: 0.6
  trend_filter:
    moving_average_days: 120
    price_relation: above
  selection:
    top_n: 2
  defense:
    assets:
      - exchange: SSE
        symbol: "511010"
costs:
  transaction_cost_bps: 5
performance:
  risk_free_rate: 0.02
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
type: dual_momentum
universe_config: {pool_path}
parameters:
  momentum:
    short_window_days: 63
    long_window_days: 126
  score_weights:
    short: 0.4
    long: 0.6
  trend_filter:
    moving_average_days: 120
    price_relation: above
  selection:
    top_n: 2
  defense:
    assets:
      - exchange: SSE
        symbol: "511010"
costs:
  transaction_cost_bps: 5
performance:
  risk_free_rate: 0.02
""",
        encoding="utf-8",
    )
    pool_path.write_text(
        """
version: 1
provider: tencent
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

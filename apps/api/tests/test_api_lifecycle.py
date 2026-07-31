from pathlib import Path

import pytest
import vela_api.main as api_main
from fastapi.testclient import TestClient
from vela_api.dependencies import get_app_config
from vela_core import ConfigError, load_app_config


def test_routine_requests_reuse_one_lifespan_config(monkeypatch) -> None:
    config = load_app_config("config/strategy_v1.yaml")
    loaded_paths: list[Path] = []

    def load_config(path: Path):
        loaded_paths.append(path)
        return config

    monkeypatch.setattr(api_main, "load_app_config", load_config)
    test_app = api_main.create_app()

    with TestClient(test_app) as client:
        assert client.get("/api/config").status_code == 200
        assert client.get("/api/dashboard").status_code == 200

    assert loaded_paths == [api_main.DEFAULT_STRATEGY_CONFIG_PATH]


def test_invalid_lifespan_config_prevents_api_startup(monkeypatch) -> None:
    def raise_config_error(path: Path):
        raise ConfigError("invalid test config", path=path)

    monkeypatch.setattr(api_main, "load_app_config", raise_config_error)

    with pytest.raises(ConfigError, match="invalid test config"):
        with TestClient(api_main.create_app()):
            pass


def test_config_dependency_override_is_scoped_to_one_application() -> None:
    default_config = load_app_config("config/strategy_v1.yaml")
    overridden_config = default_config.model_copy(
        update={"strategy": default_config.strategy.model_copy(update={"version": "test-v2"})}
    )
    overridden_app = api_main.create_app()
    other_app = api_main.create_app()
    overridden_app.dependency_overrides[get_app_config] = lambda: overridden_config

    with TestClient(overridden_app) as client:
        assert client.get("/api/config").json()["strategy"]["version"] == "test-v2"
    with TestClient(other_app) as client:
        assert client.get("/api/config").json()["strategy"]["version"] == "v1"


def test_routine_request_without_lifespan_config_does_not_reload_yaml(monkeypatch) -> None:
    test_app = api_main.create_app()

    def unexpected_load(_path: Path):
        raise AssertionError("routine request must use lifespan configuration")

    monkeypatch.setattr(api_main, "load_app_config", unexpected_load)

    with pytest.raises(AttributeError, match="app_config"):
        TestClient(test_app).get("/api/config")

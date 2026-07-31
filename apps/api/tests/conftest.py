import pytest
from vela_api.dependencies import get_app_config
from vela_api.main import app
from vela_core import load_app_config


@pytest.fixture(autouse=True)
def override_global_app_config() -> None:
    previous_overrides = app.dependency_overrides.copy()
    config = load_app_config("config/strategy_v1.yaml")
    app.dependency_overrides[get_app_config] = lambda: config
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)

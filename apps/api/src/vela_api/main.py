from contextlib import asynccontextmanager

from fastapi import FastAPI
from vela_core import load_app_config

from vela_api.backtest_router import router as backtest_router
from vela_api.config import DEFAULT_STRATEGY_CONFIG_PATH
from vela_api.database import initialize_database
from vela_api.dependencies import get_app_config, get_market_data_provider
from vela_api.errors import register_exception_handlers
from vela_api.market_router import router as market_router
from vela_api.signal_router import router as signal_router
from vela_api.system_router import router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app_config = load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)
    yield


def create_app() -> FastAPI:
    api = FastAPI(title="Vela API", lifespan=lifespan)
    initialize_database(api)
    register_exception_handlers(api)
    api.include_router(system_router)
    api.include_router(market_router)
    api.include_router(signal_router)
    api.include_router(backtest_router)
    return api


app = create_app()

__all__ = ["app", "create_app", "get_app_config", "get_market_data_provider"]

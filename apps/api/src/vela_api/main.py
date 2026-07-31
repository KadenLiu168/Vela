import logging
import re
import time
import uuid
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

logger = logging.getLogger(__name__)
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,128}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app_config = load_app_config(DEFAULT_STRATEGY_CONFIG_PATH)
    yield


def create_app() -> FastAPI:
    api = FastAPI(title="Vela API", lifespan=lifespan)
    initialize_database(api)
    register_exception_handlers(api)

    @api.middleware("http")
    async def request_observability(request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        if _REQUEST_ID_PATTERN.fullmatch(request_id) is None:
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", "<unmatched>")
            logger.info(
                "api.request.completed request_id=%s method=%s route=%s status=%s duration_ms=%.3f",
                request_id,
                request.method,
                route_path,
                status_code,
                (time.perf_counter() - started) * 1000,
            )

    api.include_router(system_router)
    api.include_router(market_router)
    api.include_router(signal_router)
    api.include_router(backtest_router)
    return api


app = create_app()

__all__ = ["app", "create_app", "get_app_config", "get_market_data_provider"]

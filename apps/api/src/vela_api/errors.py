import logging
from typing import Literal

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from vela_core import ConfigError
from vela_core.errors import BacktestDataError, InvalidDateRangeError, MissingMarketDataError

ErrorCategory = Literal["validation", "not_found", "operation_failed", "unexpected"]
logger = logging.getLogger(__name__)


def register_exception_handlers(app) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ConfigError, config_exception_handler)
    app.add_exception_handler(MissingMarketDataError, missing_market_data_exception_handler)
    app.add_exception_handler(InvalidDateRangeError, invalid_date_range_exception_handler)
    app.add_exception_handler(BacktestDataError, backtest_data_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)


async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return _error_response(422, "validation_error", "validation", "Request validation failed")


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
    return _error_response(
        exc.status_code,
        _http_error_code(exc.status_code),
        _category(exc.status_code),
        message,
    )


async def config_exception_handler(_request: Request, exc: ConfigError) -> JSONResponse:
    return _error_response(500, "config_error", "operation_failed", str(exc))


async def missing_market_data_exception_handler(
    _request: Request, _exc: MissingMarketDataError
) -> JSONResponse:
    return _error_response(
        400, "no_market_data", "operation_failed", "No local market prices found"
    )


async def invalid_date_range_exception_handler(
    _request: Request, _exc: InvalidDateRangeError
) -> JSONResponse:
    return _error_response(
        400,
        "invalid_date_range",
        "operation_failed",
        "start_date must be on or before end_date",
    )


async def backtest_data_exception_handler(
    _request: Request, exc: BacktestDataError
) -> JSONResponse:
    return _error_response(400, "operation_failed", "operation_failed", str(exc))


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "api.unexpected_exception request_id=%s exception_type=%s",
        getattr(request.state, "request_id", "unknown"),
        type(exc).__name__,
    )
    response = _error_response(500, "unexpected_error", "unexpected", "Unexpected API error")
    request_id = getattr(request.state, "request_id", None)
    if request_id is not None:
        response.headers["X-Request-ID"] = request_id
    return response


def _error_response(
    status_code: int, code: str, category: ErrorCategory, message: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "category": category, "message": message}},
    )


def _category(status_code: int) -> ErrorCategory:
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation"
    if status_code >= 500:
        return "unexpected"
    return "operation_failed"


def _http_error_code(status_code: int) -> str:
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation_error"
    if status_code >= 500:
        return "unexpected_error"
    return "operation_failed"

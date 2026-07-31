from typing import Literal

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from vela_core import ConfigError

ErrorCategory = Literal["validation", "not_found", "operation_failed", "unexpected"]


def register_exception_handlers(app) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ConfigError, config_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)


async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return _error_response(422, "validation_error", "validation", "Request validation failed")


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
    return _error_response(
        exc.status_code,
        _http_error_code(exc.status_code, message),
        _category(exc.status_code),
        message,
    )


async def config_exception_handler(_request: Request, exc: ConfigError) -> JSONResponse:
    return _error_response(500, "config_error", "operation_failed", str(exc))


async def unexpected_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return _error_response(500, "unexpected_error", "unexpected", "Unexpected API error")


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


def _http_error_code(status_code: int, message: str) -> str:
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation_error"
    if status_code >= 500:
        return "unexpected_error"
    return {
        "No local market prices found": "no_market_data",
        "start_date must be on or before end_date": "invalid_date_range",
    }.get(message, "operation_failed")

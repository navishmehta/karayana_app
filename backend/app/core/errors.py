"""Uniform API errors: every error response is {"message", "code", "errors"?}.

Raise AppError(ErrorCode.X) from services for business-rule failures.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.i18n import has_key, negotiate_locale, set_locale, t
from app.enums.error_code import ErrorCode

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Business-rule failure with a stable error code and optional field errors."""

    def __init__(self, code: ErrorCode, errors: dict[str, list[str]] | None = None, status: int | None = None):
        super().__init__(code.value)
        self.code = code
        self.errors = errors
        self.status = status or code.http_status


def error_response(
    code: ErrorCode, status: int | None = None, errors: dict | None = None, **extra: Any
) -> JSONResponse:
    body: dict[str, Any] = {"message": code.message, "code": code.value}
    if errors:
        body["errors"] = errors
    body.update(extra)
    return JSONResponse(status_code=status or code.http_status, content=body)


# HTTP status -> error code for framework-raised HTTP errors (404 route, 405 method, …)
_HTTP_STATUS_CODES: dict[int, ErrorCode] = {
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    409: ErrorCode.CONFLICT,
    429: ErrorCode.TOO_MANY_REQUESTS,
}


_LOCATION_PREFIXES = {"body", "query", "path", "header"}


def _field_name(loc: tuple[Any, ...]) -> str:
    """('body', 'items', 0, 'name') -> 'items.0.name'. Drops the 'body'/'query'/'path' prefix."""
    if loc and loc[0] in _LOCATION_PREFIXES:
        loc = loc[1:]
    return ".".join(str(part) for part in loc) or "request"


def translate_validation_error(error: dict[str, Any]) -> str:
    """Pydantic error -> translated message using locales/<lang>.json → validation.<type>."""
    field = _field_name(tuple(error.get("loc", ())))
    leaf = field.split(".")[-1]
    attribute = t(f"attributes.{leaf}") if has_key(f"attributes.{leaf}") else leaf.replace("_", " ")
    ctx = {k: v for k, v in (error.get("ctx") or {}).items() if isinstance(v, str | int | float)}

    error_type = error.get("type", "")
    # Custom validators raise ValueError("validation.some_key") to pick a specific message.
    if error_type == "value_error":
        message_key = str((error.get("ctx") or {}).get("error", ""))
        if message_key.startswith("validation.") and has_key(message_key):
            return t(message_key, attribute=attribute, **ctx)

    key = f"validation.{error_type}"
    return t(key, attribute=attribute, **ctx) if has_key(key) else t("validation.invalid", attribute=attribute)


def register_exception_handlers(app: FastAPI) -> None:
    def _use_request_locale(request: Request) -> None:
        # Handlers outside the middleware stack (500s) still answer in the caller's language.
        set_locale(negotiate_locale(request.headers.get("accept-language")))

    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        _use_request_locale(request)
        return error_response(exc.code, exc.status, exc.errors)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        _use_request_locale(request)
        errors: dict[str, list[str]] = {}
        for error in exc.errors():
            errors.setdefault(_field_name(tuple(error.get("loc", ()))), []).append(translate_validation_error(error))
        return error_response(ErrorCode.VALIDATION_FAILED, errors=errors)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        _use_request_locale(request)
        code = _HTTP_STATUS_CODES.get(exc.status_code, ErrorCode.HTTP_ERROR)
        response = error_response(code, exc.status_code)
        for name, value in (exc.headers or {}).items():
            response.headers[name] = value
        return response

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        _use_request_locale(request)
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        debug = {"exception": type(exc).__name__, "detail": str(exc)} if get_settings().debug else None
        return error_response(ErrorCode.SERVER_ERROR, **({"debug": debug} if debug else {}))

"""Stable machine-readable error codes, returned as `code` in every API error."""

from enum import StrEnum

from app.core.i18n import t


class ErrorCode(StrEnum):
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    HTTP_ERROR = "HTTP_ERROR"
    SERVER_ERROR = "SERVER_ERROR"

    @property
    def http_status(self) -> int:
        return _STATUS[self]

    @property
    def message(self) -> str:
        return t(f"errors.{self.value.lower()}")


_STATUS: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.CONFLICT: 409,
    ErrorCode.TOO_MANY_REQUESTS: 429,
    ErrorCode.HTTP_ERROR: 400,
    ErrorCode.SERVER_ERROR: 500,
}

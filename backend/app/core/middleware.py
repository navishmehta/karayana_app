"""HTTP middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants import HSTS_MAX_AGE_SECONDS
from app.core.i18n import negotiate_locale, set_locale


class LocaleMiddleware(BaseHTTPMiddleware):
    """Sets the request language from Accept-Language so every message (even 404s) is translated."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        locale = negotiate_locale(request.headers.get("accept-language"))
        set_locale(locale)
        response = await call_next(request)
        response.headers["Content-Language"] = locale
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Standard browser protections. HSTS only in production (served over HTTPS)."""

    def __init__(self, app, hsts: bool) -> None:  # noqa: ANN001
        super().__init__(app)
        self.hsts = hsts

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if self.hsts:
            response.headers.setdefault(
                "Strict-Transport-Security", f"max-age={HSTS_MAX_AGE_SECONDS}; includeSubDomains"
            )
        return response

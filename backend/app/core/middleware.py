"""HTTP middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.i18n import negotiate_locale, set_locale


class LocaleMiddleware(BaseHTTPMiddleware):
    """Sets the request language from Accept-Language so every message (even 404s) is translated."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        locale = negotiate_locale(request.headers.get("accept-language"))
        set_locale(locale)
        response = await call_next(request)
        response.headers["Content-Language"] = locale
        return response

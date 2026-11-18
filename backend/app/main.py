"""FastAPI application factory. Run locally with:  uv run fastapi dev app/main.py"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.constants import API_V1_PREFIX, MEDIA_URL_PATH, MIN_JWT_SECRET_LENGTH
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import LocaleMiddleware, SecurityHeadersMiddleware


def check_settings(settings: Settings) -> None:
    """Refuse to start with settings that would be unsafe in a real shop."""
    secret = settings.jwt_secret.get_secret_value()
    if not secret:
        raise RuntimeError("JWT_SECRET must be set (generate one with: openssl rand -hex 32)")
    if settings.is_production:
        problems = []
        if len(secret) < MIN_JWT_SECRET_LENGTH:
            problems.append(f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters")
        if settings.debug:
            problems.append("DEBUG must be false")
        if settings.mail_driver != "smtp":
            problems.append("MAIL_DRIVER must be smtp (password reset emails)")
        if problems:
            raise RuntimeError("Unsafe production settings: " + "; ".join(problems))


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.debug)
    check_settings(settings)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(LocaleMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["Content-Language"],
        )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=API_V1_PREFIX)

    if settings.media_driver == "local":  # production serves media from object storage / CDN instead
        media_root = Path(settings.media_root)
        media_root.mkdir(parents=True, exist_ok=True)
        app.mount(MEDIA_URL_PATH, StaticFiles(directory=media_root), name="media")
    return app


app = create_app()

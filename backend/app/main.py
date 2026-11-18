"""FastAPI application factory. Run locally with:  uv run fastapi dev app/main.py"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.constants import API_V1_PREFIX
from app.core.errors import register_exception_handlers
from app.core.middleware import LocaleMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(LocaleMiddleware)
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
    return app


app = create_app()

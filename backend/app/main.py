"""FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.needs import router as needs_router
from app.api.projects import router as projects_router
from app.api.settings import router as settings_router
from app.config import get_settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(title="Requirement Review Dashboard", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(needs_router, prefix="/api")
    app.include_router(models_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    return app


app = create_app()
